using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Tellurian.Trains.Communications.Channels;
using Tellurian.Trains.Protocols.LocoNet;
using Tellurian.Trains.Protocols.LocoNet.Commands;
using Tellurian.Trains.Protocols.LocoNet.Notifications;

namespace LocoNetBridge;

internal static class Program
{
    private const int BridgePort = 5555;

    private static ILoggerFactory _loggerFactory = null!;
    private static LncvBackend _backend = null!;

    static async Task Main()
    {
        _loggerFactory = LoggerFactory.Create(builder =>
        {
            builder.AddSimpleConsole();
            builder.SetMinimumLevel(LogLevel.Warning);
        });

        _backend = new LncvBackend(_loggerFactory);
        _backend.DebugTrace += Console.WriteLine;

        var listener = new TcpListener(IPAddress.Loopback, BridgePort);
        listener.Start();

        Console.WriteLine($"LocoNet Bridge escuchando en 127.0.0.1:{BridgePort}");

        while (true)
        {
            var client = await listener.AcceptTcpClientAsync();
            _ = Task.Run(() => HandleClientAsync(client));
        }
    }

    private static async Task HandleClientAsync(TcpClient client)
    {
        Console.WriteLine("Cliente Python conectado");

        using var stream = client.GetStream();
        using var reader = new StreamReader(stream, new UTF8Encoding(false));
        using var writer = new StreamWriter(stream, new UTF8Encoding(false))
        {
            AutoFlush = true
        };

        try
        {
            string? line;

            while ((line = await reader.ReadLineAsync()) != null)
            {
                line = line.Trim();

                if (line.Length == 0)
                    continue;

                Console.WriteLine($"RX PY <- {line}");

                string response;

                try
                {
                    response = await HandleCommandAsync(line);
                }
                catch (Exception ex)
                {
                    response = $"ERROR {ex.Message}";
                }

                Console.WriteLine($"TX PY -> {response}");
                await writer.WriteLineAsync(response);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error cliente: {ex.Message}");
        }

        Console.WriteLine("Cliente Python desconectado");
    }

    private static async Task<string> HandleCommandAsync(string command)
    {
        if (command == "PING")
            return "OK PONG";

        var args = ParseArgs(command);

        if (command.StartsWith("CONNECT", StringComparison.OrdinalIgnoreCase))
        {
            string ip = GetString(args, "ip", "127.0.0.1");
            int port = GetInt(args, "port", 1234);

            await _backend.ConnectAsync(ip, port);
            return "OK CONNECT";
        }

        if (command.StartsWith("DISCONNECT", StringComparison.OrdinalIgnoreCase))
        {
            await _backend.DisconnectAsync();
            return "OK DISCONNECT";
        }

        if (command.StartsWith("LNCV_START", StringComparison.OrdinalIgnoreCase))
        {
            ushort article = GetU16(args, "article", 0);
            ushort addr = GetU16(args, "addr", 0);

            await _backend.OpenSessionAsync(article, addr);
            return "OK LNCV_START";
        }

        if (command.StartsWith("LNCV_READ", StringComparison.OrdinalIgnoreCase))
        {
            ushort cv = GetU16(args, "cv", 0);
            ushort value = await _backend.ReadCvAsync(cv);

            return $"VALUE cv={cv} value={value}";
        }

        if (command.StartsWith("LNCV_WRITE", StringComparison.OrdinalIgnoreCase))
        {
            ushort cv = GetU16(args, "cv", 0);
            ushort value = GetU16(args, "value", 0);

            await _backend.WriteCvAsync(cv, value);
            return "OK LNCV_WRITE";
        }

        if (command.StartsWith("LNCV_STOP", StringComparison.OrdinalIgnoreCase))
        {
            await _backend.CloseSessionAsync();
            return "OK LNCV_STOP";
        }

        return $"ERROR Unknown command: {command}";
    }

    private static Dictionary<string, string> ParseArgs(string command)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var parts = command.Split(' ', StringSplitOptions.RemoveEmptyEntries);

        foreach (var part in parts.Skip(1))
        {
            var kv = part.Split('=', 2);

            if (kv.Length == 2)
                result[kv[0]] = kv[1];
        }

        return result;
    }

    private static string GetString(Dictionary<string, string> args, string key, string def)
    {
        return args.TryGetValue(key, out var value) ? value : def;
    }

    private static int GetInt(Dictionary<string, string> args, string key, int def)
    {
        return args.TryGetValue(key, out var text) &&
               int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out var value)
            ? value
            : def;
    }

    private static ushort GetU16(Dictionary<string, string> args, string key, ushort def)
    {
        if (!args.TryGetValue(key, out var text))
            return def;

        text = text.Trim();

        if (text.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
            return ushort.Parse(text[2..], NumberStyles.HexNumber, CultureInfo.InvariantCulture);

        return ushort.Parse(text, CultureInfo.InvariantCulture);
    }
}

internal sealed class LncvBackend : IAsyncDisposable, IObserver<CommunicationResult>
{
    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger<LncvBackend> _logger;

    private TcpLocoNetChannel? _channel;
    private IDisposable? _channelSubscription;

    private ushort? _article;
    private ushort? _moduleAddress;

    private readonly object _sync = new();
    private readonly SemaphoreSlim _opLock = new(1, 1);

    private TaskCompletionSource<LncvNotification>? _pendingSessionAck;
    private TaskCompletionSource<LncvNotification>? _pendingReadReply;
    private TaskCompletionSource<LongAcknowledge>? _pendingWriteAck;

    public event Action<string>? DebugTrace;

    public LncvBackend(ILoggerFactory loggerFactory)
    {
        _loggerFactory = loggerFactory;
        _logger = loggerFactory.CreateLogger<LncvBackend>();
    }

    public async Task ConnectAsync(string ip, int port)
    {
        Trace($"CONNECT -> {ip}:{port}");

        await DisconnectAsync();

        var channelLogger = _loggerFactory.CreateLogger<TcpLocoNetChannel>();
        _channel = new TcpLocoNetChannel(new TcpStreamAdapter(ip, port), channelLogger);

        _channelSubscription = _channel.Subscribe(this);
        await _channel.StartReceiveAsync();

        Trace("CONNECT OK");
    }

    public async Task DisconnectAsync()
    {
        Trace("DISCONNECT");

        _article = null;
        _moduleAddress = null;

        lock (_sync)
        {
            _pendingSessionAck?.TrySetCanceled();
            _pendingReadReply?.TrySetCanceled();
            _pendingWriteAck?.TrySetCanceled();

            _pendingSessionAck = null;
            _pendingReadReply = null;
            _pendingWriteAck = null;
        }

        _channelSubscription?.Dispose();
        _channelSubscription = null;

        if (_channel != null)
        {
            await _channel.DisposeAsync();
            _channel = null;
        }

        Trace("DISCONNECTED");
    }

    public async Task OpenSessionAsync(ushort article, ushort moduleAddress)
    {
        await _opLock.WaitAsync();

        try
        {
            EnsureConnected();

            Trace($"LNCV OPEN SESSION -> article={article}, module={moduleAddress}");

            var tcs = NewPendingSessionAck();

            var data = CustomLncvCommandBuilder.StartSession(article, moduleAddress);
            await SendBytesAsync(data);

            var reply = await WaitWithTimeout(
                tcs.Task,
                "Timeout esperando confirmación de sesión LNCV."
            );

            if (reply.LncvType != LncvMessageType.SessionAcknowledgment)
                throw new InvalidOperationException("La respuesta no es SessionAcknowledgment.");

            if (reply.ArticleNumber != article)
                throw new InvalidOperationException(
                    $"Artículo inesperado. Esperado={article}, recibido={reply.ArticleNumber}."
                );

            if (reply.ModuleAddress != moduleAddress && moduleAddress != 0xFFFF)
                throw new InvalidOperationException(
                    $"Módulo inesperado. Esperado={moduleAddress}, recibido={reply.ModuleAddress}."
                );

            _article = article;
            _moduleAddress = reply.ModuleAddress;

            Trace($"LNCV SESSION ACK <- article={reply.ArticleNumber}, module={reply.ModuleAddress}");
        }
        finally
        {
            _opLock.Release();
        }
    }

    public async Task CloseSessionAsync()
    {
        await _opLock.WaitAsync();

        try
        {
            EnsureSession();

            Trace($"LNCV CLOSE SESSION -> article={_article!.Value}, module={_moduleAddress!.Value}");

            var cmd = new LncvEndSessionCommand(_article.Value, _moduleAddress.Value);
            var raw = cmd.GetBytesWithChecksum();
            var patched = LocoNetRawHelper.PatchWorkingLncvDestination(raw);

            await SendBytesAsync(patched);

            _article = null;
            _moduleAddress = null;
        }
        finally
        {
            _opLock.Release();
        }
    }

    public async Task<ushort> ReadCvAsync(ushort cv)
    {
        await _opLock.WaitAsync();

        try
        {
            return await ReadLncvValueWithRetryAsync(cv, 2);
        }
        finally
        {
            _opLock.Release();
        }
    }

    public async Task WriteCvAsync(ushort cv, ushort value)
    {
        await _opLock.WaitAsync();

        try
        {
            await WriteLncvValueCoreAsync(cv, value);
        }
        finally
        {
            _opLock.Release();
        }
    }

    private async Task<ushort> ReadLncvValueWithRetryAsync(ushort cv, int maxAttempts)
    {
        Exception? lastError = null;

        for (int attempt = 1; attempt <= maxAttempts; attempt++)
        {
            try
            {
                EnsureSession();

                Trace($"LNCV READ REQ -> CV={cv} try={attempt}/{maxAttempts}");

                var tcs = NewPendingReadReply();

                var data = CustomLncvCommandBuilder.Read(
                    _article!.Value,
                    cv,
                    _moduleAddress!.Value
                );

                await SendBytesAsync(data);

                var reply = await WaitWithTimeout(
                    tcs.Task,
                    $"Timeout leyendo LNCV[{cv}].",
                    6000
                );

                if (reply.LncvType != LncvMessageType.ReadReply)
                    throw new InvalidOperationException($"Respuesta no válida para LNCV[{cv}].");

                if (reply.ArticleNumber != _article.Value)
                    throw new InvalidOperationException(
                        $"Artículo inesperado al leer LNCV[{cv}]. Esperado={_article.Value}, recibido={reply.ArticleNumber}."
                    );

                if (reply.CvNumber != cv)
                    throw new InvalidOperationException(
                        $"CV inesperada. Esperada={cv}, recibida={reply.CvNumber}."
                    );

                Trace($"LNCV READ OK <- CV={reply.CvNumber}, VALUE={reply.CvValue}");
                return reply.CvValue;
            }
            catch (Exception ex)
            {
                lastError = ex;
                Trace($"LNCV READ FAIL <- CV={cv}, try={attempt}, error={ex.Message}");

                if (attempt < maxAttempts)
                    await Task.Delay(700);
            }
        }

        throw lastError ?? new TimeoutException($"No se pudo leer LNCV[{cv}].");
    }

    private async Task WriteLncvValueCoreAsync(ushort cv, ushort value)
    {
        EnsureSession();

        Trace($"LNCV WRITE REQ -> CV={cv}, VALUE={value}");

        var tcs = NewPendingWriteAck();

        var data = CustomLncvCommandBuilder.Write(_article!.Value, cv, value);
        await SendBytesAsync(data);

        var ack = await WaitWithTimeout(
            tcs.Task,
            $"Timeout escribiendo LNCV[{cv}] = {value}.",
            8000
        );

        if (ack.ForOperationCode != 0xED)
            throw new InvalidOperationException(
                $"ACK no corresponde a LNCV. Opcode=0x{ack.ForOperationCode:X2}."
            );

        Trace($"LNCV WRITE ACK <- opcode=0x{ack.ForOperationCode:X2}, success={ack.IsSuccess}");

        if (!ack.IsSuccess)
            throw new InvalidOperationException($"El módulo rechazó LNCV[{cv}] = {value}.");

        await Task.Delay(250);

        ushort readBack = await ReadLncvValueWithRetryAsync(cv, 2);

        Trace($"LNCV WRITE VERIFY <- CV={cv}, expected={value}, readBack={readBack}");

        if (readBack != value)
            throw new InvalidOperationException(
                $"Verificación fallida LNCV[{cv}]. Esperado={value}, leído={readBack}."
            );
    }

    private async Task SendBytesAsync(byte[] data)
    {
        EnsureConnected();

        Trace($"TX RAW -> {Hex(data)}");

        var result = await _channel!.SendAsync(data);

        if (!result.IsSuccess)
            throw new InvalidOperationException("No se pudo enviar el comando al canal LocoNet.");

        Trace("TX OK");
    }

    private TaskCompletionSource<LncvNotification> NewPendingSessionAck()
    {
        lock (_sync)
        {
            _pendingSessionAck?.TrySetCanceled();

            _pendingSessionAck = new TaskCompletionSource<LncvNotification>(
                TaskCreationOptions.RunContinuationsAsynchronously
            );

            return _pendingSessionAck;
        }
    }

    private TaskCompletionSource<LncvNotification> NewPendingReadReply()
    {
        lock (_sync)
        {
            _pendingReadReply?.TrySetCanceled();

            _pendingReadReply = new TaskCompletionSource<LncvNotification>(
                TaskCreationOptions.RunContinuationsAsynchronously
            );

            return _pendingReadReply;
        }
    }

    private TaskCompletionSource<LongAcknowledge> NewPendingWriteAck()
    {
        lock (_sync)
        {
            _pendingWriteAck?.TrySetCanceled();

            _pendingWriteAck = new TaskCompletionSource<LongAcknowledge>(
                TaskCreationOptions.RunContinuationsAsynchronously
            );

            return _pendingWriteAck;
        }
    }

    private static async Task<T> WaitWithTimeout<T>(
        Task<T> task,
        string message,
        int timeoutMs = 8000
    )
    {
        var completed = await Task.WhenAny(task, Task.Delay(timeoutMs));

        if (completed != task)
            throw new TimeoutException(message);

        return await task;
    }

    private void EnsureConnected()
    {
        if (_channel == null)
            throw new InvalidOperationException("No hay conexión LocoNet activa.");
    }

    private void EnsureSession()
    {
        EnsureConnected();

        if (!_article.HasValue || !_moduleAddress.HasValue)
            throw new InvalidOperationException("No hay sesión LNCV abierta.");
    }

    public void OnNext(CommunicationResult value)
    {
        if (value is not SuccessResult success)
            return;

        var data = success.Data();

        if (data == null || data.Length == 0)
            return;

        Trace($"RX RAW <- {Hex(data)}");

        try
        {
            var message = LocoNetMessageFactory.Create(data);

            switch (message)
            {
                case LncvNotification lncv:
                    Trace($"RX LNCV <- type={lncv.LncvType}, article={lncv.ArticleNumber}, cv={lncv.CvNumber}, value={lncv.CvValue}, module={lncv.ModuleAddress}");
                    break;

                case LongAcknowledge ack:
                    Trace($"RX LONG ACK <- forOpcode=0x{ack.ForOperationCode:X2}, success={ack.IsSuccess}");
                    break;

                default:
                    if (data[0] == 0xED)
                        Trace("RX ECHO <- comando reenviado por gateway");
                    else
                        Trace($"RX AUX <- {message.GetType().Name}");
                    break;
            }

            lock (_sync)
            {
                if (message is LncvNotification lncv)
                {
                    if (lncv.LncvType == LncvMessageType.SessionAcknowledgment)
                    {
                        _pendingSessionAck?.TrySetResult(lncv);
                        _pendingSessionAck = null;
                        return;
                    }

                    if (lncv.LncvType == LncvMessageType.ReadReply)
                    {
                        _pendingReadReply?.TrySetResult(lncv);
                        _pendingReadReply = null;
                        return;
                    }
                }

                if (message is LongAcknowledge ack && ack.ForOperationCode == 0xED)
                {
                    _pendingWriteAck?.TrySetResult(ack);
                    _pendingWriteAck = null;
                }
            }
        }
        catch (Exception ex)
        {
            Trace($"RX PARSE ERROR <- {ex.Message}");
            _logger.LogError(ex, "Error procesando mensaje LocoNet.");
        }
    }

    public void OnError(Exception error)
    {
        Trace($"CHANNEL ERROR <- {error.Message}");

        lock (_sync)
        {
            _pendingSessionAck?.TrySetException(error);
            _pendingReadReply?.TrySetException(error);
            _pendingWriteAck?.TrySetException(error);

            _pendingSessionAck = null;
            _pendingReadReply = null;
            _pendingWriteAck = null;
        }
    }

    public void OnCompleted()
    {
        Trace("CHANNEL COMPLETED");

        lock (_sync)
        {
            _pendingSessionAck?.TrySetCanceled();
            _pendingReadReply?.TrySetCanceled();
            _pendingWriteAck?.TrySetCanceled();

            _pendingSessionAck = null;
            _pendingReadReply = null;
            _pendingWriteAck = null;
        }
    }

    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();
        _opLock.Dispose();
    }

    private void Trace(string text)
    {
        DebugTrace?.Invoke($"[{DateTime.Now:HH:mm:ss.fff}] {text}");
    }

    private static string Hex(byte[] data)
    {
        return string.Join(" ", data.Select(b => b.ToString("X2", CultureInfo.InvariantCulture)));
    }
}

internal static class CustomLncvCommandBuilder
{
    private const byte OpCode = 0xED;
    private const byte MessageLength = 0x0F;
    private const byte Source = 0x01;

    private const byte DestinationLow = 0x05;
    private const byte DestinationHigh = 0x00;

    private const byte CmdReadOrSession = 0x21;
    private const byte CmdWrite = 0x20;
    private const byte CmdDataPron = 0x80;
    private const byte CmdDataNone = 0x00;

    public static byte[] StartSession(ushort articleNumber, ushort moduleAddress)
    {
        return Create(CmdReadOrSession, articleNumber, 0, moduleAddress, CmdDataPron);
    }

    public static byte[] Read(ushort articleNumber, ushort cvNumber, ushort moduleAddress)
    {
        return Create(CmdReadOrSession, articleNumber, cvNumber, moduleAddress, CmdDataNone);
    }

    public static byte[] Write(ushort articleNumber, ushort cvNumber, ushort value)
    {
        return Create(CmdWrite, articleNumber, cvNumber, value, CmdDataNone);
    }

    private static byte[] Create(
        byte cmd,
        ushort articleNumber,
        ushort cvNumber,
        ushort moduleOrValue,
        byte cmdData
    )
    {
        byte[] payload =
        {
            (byte)(articleNumber & 0xFF),
            (byte)(articleNumber >> 8),
            (byte)(cvNumber & 0xFF),
            (byte)(cvNumber >> 8),
            (byte)(moduleOrValue & 0xFF),
            (byte)(moduleOrValue >> 8),
            cmdData
        };

        byte pxct1 = Pxct1Helper.Encode(payload);

        byte[] msg =
        {
            OpCode,
            MessageLength,
            Source,
            DestinationLow,
            DestinationHigh,
            cmd,
            pxct1,
            payload[0],
            payload[1],
            payload[2],
            payload[3],
            payload[4],
            payload[5],
            payload[6]
        };

        return Message.AppendChecksum(msg);
    }
}

internal static class Pxct1Helper
{
    public static byte Encode(byte[] data)
    {
        if (data.Length != 7)
            throw new ArgumentException("PXCT1 requiere exactamente 7 bytes.", nameof(data));

        byte pxct1 = 0;

        for (int i = 0; i < 7; i++)
        {
            if ((data[i] & 0x80) != 0)
            {
                pxct1 |= (byte)(1 << i);
                data[i] &= 0x7F;
            }
        }

        return pxct1;
    }
}

internal static class LocoNetRawHelper
{
    public static byte[] PatchWorkingLncvDestination(byte[] original)
    {
        var data = (byte[])original.Clone();

        data[3] = 0x05;
        data[4] = 0x00;
        data[^1] = CalculateChecksum(data.AsSpan(0, data.Length - 1));

        return data;
    }

    public static byte CalculateChecksum(ReadOnlySpan<byte> dataWithoutChecksum)
    {
        byte checksum = 0xFF;

        foreach (byte b in dataWithoutChecksum)
            checksum ^= b;

        return checksum;
    }
}