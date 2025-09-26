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

    def devices_to_cards(self, server_type, devices):
        cards = []
        lastone = lambda : {"type": server_type} if len(cards) == 0 else cards[-1]
        for device in devices:
            card = lastone()
            card_id = card.get("card_id")
            if card_id is None:
                card["card_id"] = device["card_id"]
                chips = [device]
                card["devices"] = chips
                cards.append(card)
            elif card_id == device["card_id"]:
                chips = card["devices"]
                chips.append(device)
                card["devices"] = chips
                card["power"] = self.get_card_power(card)
            else:
                card = {"type": server_type,
                        "card_id": device["card_id"],
                        "devices": [device]}
                cards.append(card)
        return cards

    def get_card_entry(self):
        cmd = "ascend-dmi -i --format json"  # 使用Ascend-DMI做实时信息统计
        ascend_info_json = json.loads(os.popen(cmd).read())

        card_entry_list = []
        hardware_brief = ascend_info_json.get("hardware_brief")
        if hardware_brief is None:
            return card_entry_list
        cards = hardware_brief.get("cards")
        if cards is None:
            cards = []
            server = hardware_brief.get("server")
            if server is None:
                return card_entry_list
            server_type = server.get("type")
            if server_type is None:
                return card_entry_list
            devices = server.get("devices")
            if devices is None:
                return card_entry_list
            cards = self.devices_to_cards(server_type, devices)
        for card_info in cards:
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

    def parse_power(self, pw):
        power = 0.0
        pw = pw.strip()
        if pw.endswith("W"):
            pw = pw[:-1].strip()
            try:
                power = float(pw)
            except Exception:
                return power
            return power

    def get_power(self, power):
        power = self.parse_power(power)
        return f"{power:.2f} W"

    def get_card_power(self, card):
        chips = card.get("devices", {})
        power = 0.0
        for chip in chips:
            power += self.parse_power(
                chip.get("power_information", {}).get(
                    "realtime_power", "0.00 W"))
        return f"{power:.2f} W"
