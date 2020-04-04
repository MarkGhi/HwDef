import time
import threading
import platform
import subprocess

import npyscreen
import psutil


class App(npyscreen.StandardApp):
    def onStart(self):
        npyscreen.setTheme(npyscreen.Themes.TransparentThemeLightText)
        self.addForm("MAIN", MainForm, name="HwDef")


class MainForm(npyscreen.FormBaseNew):
    def create(self):
        y, x = self.useable_space()

        self.add_event_hander("event_menu_select", self.event_menu_select)

        self.menu_list = self.add(MenuList,
                                  name="Menu",
                                  values=["General", "Cpu", "Ram", "Disk", "Network"],
                                  max_width=x // 4)

        self.info_box = self.add(InfoBox,
                                 name="Info",
                                 relx=x // 4 + 5,
                                 rely=2)
        self.info_box.create()

    def event_menu_select(self, event):
        self.info_box.update_info(self.menu_list.value)


class InfoBox(npyscreen.BoxTitle):
    def create(self, **kwargs):
        self._can_update = True
        self.set_general_info()

    def get_processor_name(self):
        if platform.system() == "Windows":
            return platform.processor()
        elif platform.system() == "Darwin":
            return subprocess.check_output(['/usr/sbin/sysctl', "-n", "machdep.cpu.brand_string"]).strip()
        elif platform.system() == "Linux":
            command = "cat /proc/cpuinfo"
            return subprocess.check_output(command, shell=True).strip()
        return ""

    def get_size(self, bytes, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    def set_general_info(self):
        uname = platform.uname()

        self.values = [
            "",
            f"System: {uname.system}",
            f"Node Name: {uname.node}",
            f"Release: {uname.release}",
            f"Version: {uname.version}",
            f"Machine: {uname.machine}",
            f"Processor: {uname.processor}"
        ]

        self.display()

    def set_cpu_info(self):
        cpufreq = psutil.cpu_freq()

        self.values = [
            "",
            self.get_processor_name().decode('utf-8'),
            "",
            "Physical cores: %s" % str(
                psutil.cpu_count(logical=False)),
            "Total cores: %s" % str(
                psutil.cpu_count(logical=True)),
            f"Max Frequency: {cpufreq.max:.2f}Mhz",
            f"Min Frequency: {cpufreq.min:.2f}Mhz"
        ]

        while self._can_update:
            # Clear list for new updated values
            if len(self.values) > 7:
                del self.values[7:]

            self.values.append(f"Current Frequency: {cpufreq.current:.2f}Mhz")

            for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
                self.values.append(f"Core {i}: {percentage}%")

            self.values.append(f"Total CPU Usage: {psutil.cpu_percent()}%")

            self.display()
            time.sleep(1)

    def set_ram_info(self):
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        self.values = [
            "",
            "Memory",
            f"Total: {self.get_size(svmem.total)}",
            f"Available: {self.get_size(svmem.available)}",
            f"Used: {self.get_size(svmem.used)}",
            f"Percentage: {svmem.percent}%",
            "",
            "Swap",
            f"Total: {self.get_size(swap.total)}",
            f"Free: {self.get_size(swap.free)}",
            f"Used: {self.get_size(swap.used)}",
            f"Percentage: {swap.percent}%"
        ]

        self.display()

    def update_info(self, selected_item):
        # Permit to the thread to update info_box value, set to False to interrupt any running thread
        self._can_update = False

        if selected_item == 0:
            self.set_general_info()
        elif selected_item == 1:
            # Set to True to allow thread to run
            self._can_update = True
            threading.Thread(target=self.set_cpu_info).start()
        elif selected_item == 2:
            self.set_ram_info()


class MenuList(npyscreen.BoxTitle):
    def __init__(self, *args, **keywords):
        super(MenuList, self).__init__(*args, **keywords)

    def when_value_edited(self):
        self.parent.parentApp.queue_event(npyscreen.Event("event_menu_select"))


if __name__ == '__main__':
    App().run()
