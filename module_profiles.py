MODULE_PROFILES = {
    "turnout": {
        "article": 6030,
        "lncvs": {
            0: "module_addr",
            1: "turnout_addr_1",
            2: "turnout_addr_2",
            5: "type",
            7: "invert_dir",
            8: "invert_fb",
            9: "has_feedback",
        }
    },

    "signal": {
        "article": 6020,
        "lncvs": {
            0: "module_addr",
            1: "signal_addr_1",
            2: "signal_addr_2",
            3: "signal_addr_3",
            5: "signal_type",
            12: "signal_group",
        }
    },

    "rm": {
        "article": 6040,
        "lncvs": {
            0: "module_addr",
            1: "sensor_1",
            2: "sensor_2",
            5: "rm_type",
        }
    },

    "button": {
        "article": 6050,
        "lncvs": {
            0: "module_addr",
            1: "button_id",
            2: "target_module",
            3: "action_type",
        }
    }
}