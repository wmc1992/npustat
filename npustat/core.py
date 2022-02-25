#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import locale
import os
import platform
import sys
from datetime import datetime

from blessed import Terminal
from six.moves import cStringIO as StringIO

from .ascend_dmi import GetCardStatusWithAscendDmi
from .npu_smi import GetCardStatusWithNpuSmi

IS_WINDOWS = "windows" in platform.platform().lower()


class Chip:
    """ 每个Atlas加速卡中会有多个芯片，该类表示每个芯片的信息 """

    def __init__(self, entry, term, *args, **kwargs):
        if not isinstance(entry, dict):
            raise TypeError("entry should be a dict, {} given".format(type(entry)))
        self.entry = entry

        self.term = term

    def __repr__(self):
        return self.print_to(StringIO()).getvalue()

    def keys(self):
        return self.entry.keys()

    def __getitem__(self, key):
        return self.entry[key]

    @property
    def chip_id(self):
        return self.entry["chip_id"]

    @property
    def chip_name(self):
        return self.entry["chip_name"]

    @property
    def device_id(self):
        return self.entry["device_id"]

    @property
    def health(self):
        return self.entry["health"]

    @property
    def temperature(self):
        return self.entry["temperature"]

    @property
    def ai_core_usage(self):
        return self.entry["ai_core_usage"]

    @property
    def memory_used(self):
        return self.entry["memory_used"]

    @property
    def memory_total(self):
        return self.entry["memory_total"]

    def get_color(self):
        def _conditional(cond_fn, true_value, false_value, error_value=self.term.bold_black):
            try:
                return cond_fn() and true_value or false_value
            except Exception:
                return error_value

        colors = dict()
        colors["C0"] = self.term.normal
        colors["C1"] = self.term.cyan
        colors["CBold"] = self.term.bold
        colors["ChipName"] = self.term.blue
        colors["ChipTemp"] = _conditional(lambda: self.temperature < 60, self.term.red, self.term.bold_red)
        colors["ChipMemU"] = self.term.bold_yellow
        colors["ChipMemT"] = self.term.yellow
        colors["ChipHealth"] = _conditional(lambda: self.health == "OK", self.term.green, self.term.bold_red)
        colors["ChipAICore"] = _conditional(lambda: self.ai_core_usage < 50, self.term.green, self.term.bold_green)
        return colors

    def print_to(self, fp, chip_name_width=16, device_id_width=1, *args, **kwargs):
        colors = self.get_color()

        # build one-line display information
        reps = ""
        reps += "%(C1)s[{entry[chip_id]}]%(C0)s" + " "
        reps += "%(C1)s[{entry[device_id]:>{device_id_width}}]%(C0)s" + " "
        reps += "%(ChipHealth)s{entry[health]}%(C0)s" + ", "
        reps += "%(ChipName)s{entry[chip_name]:{chip_name_width}}%(C0)s" + " |"
        reps += "%(ChipTemp)s{entry[temperature]:>3}°C%(C0)s" + ", "
        reps += "%(ChipAICore)s{entry[ai_core_usage]:>3} %%%(C0)s, "
        reps += "%(C1)s%(ChipMemU)s{entry[memory_used]:>5}%(C0)s" + " / " + "%(ChipMemT)s{entry[memory_total]:>5}%(C0)s"

        def _repr(v, none_value="??"):
            return none_value if v is None else v

        reps = reps % colors
        reps = reps.format(entry={k: _repr(v) for k, v in self.entry.items()},
                           chip_name_width=chip_name_width, device_id_width=device_id_width)
        fp.write(reps)
        return fp

    def get_print_len(self, chip_name_width=16, device_id_width=1):
        """ 获取当前芯片打印出来之后的长度 """
        my_length = len(str(self.chip_id)) + len("[]") + len(" ") + \
                    max(len(str(self.device_id)), device_id_width) + len("[]") + len(" ") + \
                    len(str(self.health)) + len(", ") + \
                    max(len(str(self.chip_name)), chip_name_width) + len(" | ") + \
                    len(str(self.temperature)) + len("°C") + len(", ") + \
                    max(len(str(self.ai_core_usage)), 3) + len(" %") + len(", ") + \
                    max(len(str(self.memory_used)), 5) + len(" / ") + max(len(str(self.memory_total)), 5)
        return my_length

    def jsonify(self):
        o = self.entry.copy()

        # todo 目前还没有任何方法获取进程信息，见: https://bbs.huaweicloud.com/forum/thread-173510-1-1.html
        # if self.entry["processes"] is not None:
        #     o["processes"] = [{k: v for (k, v) in p.items() if k != "gpu_uuid"} for p in self.entry["processes"]]
        return o


class AtlasCard:
    """ Atlas加速卡 """

    def __init__(self, entry, show_power, eol_char, term, *args, **kwargs):
        if not isinstance(entry, dict):
            raise TypeError("entry should be a dict, {} given".format(type(entry)))
        self.entry = entry

        chip_list = []
        for chip_entry in entry["chip_entry_list"]:
            chip_list.append(Chip(chip_entry, term, *args, **kwargs))
        self.chip_list = chip_list

        self.show_power = show_power
        self.eol_char = eol_char
        self.term = term

    @property
    def card_id(self):
        return self.entry["card_id"]

    @property
    def type(self):
        return self.entry["type"]

    @property
    def power(self):
        return self.entry["power"]

    def get_color(self):
        colors = dict()
        colors["C0"] = self.term.normal
        colors["C1"] = self.term.cyan
        colors["CBold"] = self.term.bold
        colors["CardType"] = self.term.bold_white
        colors["CardPower"] = self.term.magenta
        return colors

    def print_to(self, fp, card_type_width=16, chip_name_width=16, device_id_width=1, *args, **kwargs):
        colors = self.get_color()

        reps = ""
        reps += "%(C1)s[{entry[card_id]}]%(C0)s" + ", "
        reps += "%(CardType)s{entry[type]:{card_type_width}}%(C0)s, "

        if self.show_power:
            reps += "%(CardPower)s{entry[power]:>3}%(C0)s"

        def _repr(v, none_value="??"):
            return none_value if v is None else v

        reps = reps % colors
        reps = reps.format(entry={k: _repr(v) for k, v in self.entry.items()}, card_type_width=card_type_width)
        fp.write(reps)
        fp.write(self.eol_char)

        # body
        for chip in self:
            chip.print_to(fp, chip_name_width=chip_name_width, device_id_width=device_id_width)
            fp.write(self.eol_char)
        return fp

    def jsonify(self):
        result = {"card_id": self.card_id, "type": self.type, }
        if self.show_power:
            result["power"] = self.power
        result["chips"] = [c.jsonify() for c in self]
        return result

    def __len__(self):
        return len(self.chip_list)

    def __iter__(self):
        return iter(self.chip_list)

    def __getitem__(self, index):
        return self.chip_list[index]


class AtlasCardCollection:
    """ 当前机器上所有atlas加速卡的信息 """

    def __init__(self, card_entry_list, version, show_power=True, no_header=True, no_title=False,
                 eol_char=os.linesep, force_color=False, compact=False, *args, **kwargs):
        self.hostname = platform.node()
        self.query_time = datetime.now()

        self.version = version
        self.show_power = show_power
        self.no_header = no_header
        self.no_title = no_title
        self.eol_char = eol_char
        self.compact = compact

        self.term = self.get_term(force_color)
        if not no_title:
            self.title_colors = self.get_title_colors()

        atlas_card_list = []
        for card_entry in card_entry_list:
            atlas_card_list.append(AtlasCard(card_entry, show_power, eol_char, self.term, *args, **kwargs))
        self.atlas_card_list = atlas_card_list

    def get_term(self, force_color=False):
        if force_color:
            TERM = os.getenv("TERM") or "xterm-256color"
            t_color = Terminal(kind=TERM, force_styling=True)

            # workaround of issue #32 (watch doesn"t recognize sgr0 characters)
            t_color._normal = u"\x1b[0;10m"
        else:
            t_color = Terminal()  # auto, depending on isatty
        return t_color

    def get_title_colors(self):
        colors = dict()
        colors["C0"] = self.term.normal
        colors["C1"] = self.term.cyan
        colors["CBold"] = self.term.bold
        colors["CardType"] = self.term.white

        colors["ChipName"] = self.term.blue
        colors["ChipTemp"] = self.term.red
        colors["ChipMemU"] = self.term.bold_yellow
        colors["ChipMemT"] = self.term.yellow
        colors["ChipHealth"] = self.term.green
        colors["ChipAICore"] = self.term.green
        colors["CardPower"] = self.term.magenta
        return colors

    def print_header(self, fp, eol_char, term, card_type_width):
        if IS_WINDOWS:
            # no localization is available; just use a reasonable default same as str(time_str) but without ms
            time_str = self.query_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_format = locale.nl_langinfo(locale.D_T_FMT)
            time_str = self.query_time.strftime(time_format)
        header_template = "{t.bold_white}{hostname:{width}}{t.normal}  "
        header_template += "{time_str}  "
        header_template += "{t.bold_black}{driver_version}{t.normal}"

        header_msg = header_template.format(
            hostname=self.hostname,
            width=card_type_width + 3,  # len("[?]")
            time_str=time_str,
            driver_version=self.version,
            t=term,
        )

        fp.write(header_msg.strip())
        fp.write(eol_char)

    def print_title(self, fp, eol_char, title_len):
        if not self.compact:
            fp.write("=" * title_len)
            fp.write(eol_char)

        title = "%(C1)s[加速卡ID]%(C0)s" + ", "
        title += "%(CardType)s加速卡类型%(C0)s, "
        if self.show_power:
            title += "%(CardPower)s功率%(C0)s"
        title = title % self.title_colors
        fp.write(title.strip())
        fp.write(eol_char)

        title = "%(C1)s[芯片ID]%(C0)s" + " "
        title += "%(C1)s[DeviceID]%(C0)s" + " "
        title += "%(ChipHealth)sHealth%(C0)s" + ", "
        title += "%(ChipName)s芯片名称%(C0)s" + " | "
        title += "%(ChipTemp)s温度%(C0)s" + ", "
        title += "%(ChipAICore)sAICore%(C0)s, "
        title += "%(C1)s%(ChipMemU)s内存%(C0)s"
        title = title % self.title_colors
        fp.write(title.strip())
        fp.write(eol_char)

        if not self.compact:
            fp.write("=" * title_len)
            fp.write(eol_char)
            fp.write(eol_char)

    def print_formatted(self, fp=sys.stdout, *args, **kwargs):
        # appearance settings
        card_type_width = [len(atlas_card.entry["type"]) for atlas_card in self]
        card_type_width = max([0] + card_type_width)
        chip_name_width = [len(chip.entry["chip_name"]) for atlas_card in self for chip in atlas_card]
        chip_name_width = max([0] + chip_name_width)
        device_id_width = [len(str(chip.entry["device_id"])) for atlas_card in self for chip in atlas_card]
        device_id_width = max([0] + device_id_width)

        # header
        if not self.no_header:
            self.print_header(fp=fp, eol_char=self.eol_char, term=self.term, card_type_width=card_type_width)

        # title
        if not self.no_title:
            title_len = 66
            if self.atlas_card_list:
                if self.atlas_card_list[0]:
                    title_len = self.atlas_card_list[0][0].get_print_len(chip_name_width, device_id_width)
            self.print_title(fp=fp, eol_char=self.eol_char, title_len=title_len)

        # body
        for atlas_card in self:
            atlas_card.print_to(fp, card_type_width=card_type_width, chip_name_width=chip_name_width,
                                device_id_width=device_id_width)
            if not self.compact:
                fp.write(self.eol_char)

        # todo 现在机器上只有4张卡，测试有8张加速卡时是否会一个屏幕显示不完整
        # for atlas_card in self:
        #     atlas_card.print_to(fp, card_type_width=card_type_width, chip_name_width=chip_name_width,
        #                         device_id_width=device_id_width)
        #     if not self.compact:
        #         fp.write(self.eol_char)
        fp.flush()
        return fp

    def jsonify(self):
        return {
            "hostname": self.hostname,
            "query_time": self.query_time,
            "atlas_cards": [atlas_card.jsonify() for atlas_card in self]
        }

    def print_json(self, fp=sys.stdout):
        def date_handler(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            else:
                raise TypeError(type(obj))

        o = self.jsonify()
        json.dump(o, fp, indent=4, separators=(",", ": "), default=date_handler)
        fp.write(os.linesep)
        fp.flush()

    def __len__(self):
        return len(self.atlas_card_list)

    def __iter__(self):
        return iter(self.atlas_card_list)

    def __getitem__(self, index):
        return self.atlas_card_list[index]

    def __repr__(self):
        s = "AtlasCardCollection(host=%s, [\n" % self.hostname
        s += "\n".join("  " + str(g) for g in self.atlas_card_list)
        s += "\n])"
        return s


def new_query(has_ascend_dmi, *args, **kwargs):
    """Query the information of all the Atlas Card on local machine"""

    if has_ascend_dmi:
        version, card_entry_list = GetCardStatusWithAscendDmi().new_query()
    else:
        version, card_entry_list = GetCardStatusWithNpuSmi().new_query()

    return AtlasCardCollection(card_entry_list, version=version, *args, **kwargs)
