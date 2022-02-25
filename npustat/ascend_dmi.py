#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os


class GetCardStatusWithAscendDmi:

    def new_query(self):
        version = self.get_version()
        card_entry_list = self.get_card_entry()
        return version, card_entry_list

    def get_version(self):
        cmd = "ascend-dmi -v"  # 获取Ascend-DMI的版本
        return os.popen(cmd).read().strip()

    def get_card_entry(self):
        cmd = "ascend-dmi -i --format json"  # 使用Ascend-DMI做实时信息统计
        ascend_info_json = json.loads(os.popen(cmd).read())

        card_entry_list = []
        for card_info in ascend_info_json["hardware_brief"]["cards"]:
            card_entry = dict()
            card_entry["card_id"] = card_info["card_id"]
            card_entry["type"] = card_info["type"]
            card_entry["power"] = self.get_power(card_info["power"])

            chip_entry_list = []
            for chip_info in card_info["devices"]:
                chip_entry = dict()
                chip_entry["chip_id"] = chip_info["chip_id"]
                chip_entry["device_id"] = chip_info["device_id"]
                chip_entry["health"] = chip_info["health"]
                chip_entry["chip_name"] = chip_info["chip_name"]
                chip_entry["temperature"] = self.get_temperature(chip_info["temperature"])
                chip_entry["ai_core_usage"] = self.get_ai_core_usage(chip_info["ai_core_information"]["ai_core_usage"])
                chip_entry["memory_used"] = chip_info["memory_information"]["used"]
                chip_entry["memory_total"] = chip_info["memory_information"]["total"]
                chip_entry_list.append(chip_entry)
            card_entry["chip_entry_list"] = chip_entry_list
            card_entry_list.append(card_entry)
        return card_entry_list

    def get_ai_core_usage(self, ai_core_usage):
        s = str(ai_core_usage).strip()
        if s.endswith("%"):
            s = s[:-1].strip()
        if isinstance(s, str) and s.isdigit():
            s = int(s)
        return s

    def get_temperature(self, temp):
        if temp.endswith("C"):
            temp = temp[:-1].strip()
        if isinstance(temp, str) and temp.isdigit():
            temp = int(temp)
        return temp

    def get_power(self, power):
        power = power.strip()
        if power.endswith("W"):
            power = power[:-1].strip()
        try:
            power = float(power)
            return f"{power:.2f} W"
        except Exception:
            return f"{power} W"
