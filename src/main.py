flatsweepVersion = "v2025.10.7"

import sys
import gi
from os import listdir
import os
from pathlib import Path
import shutil
import threading
import textwrap
import locale
from functools import partial

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib

try:
    locale.setlocale(locale.LC_ALL, os.getenv("LANG"))
except:
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

currentLanguage = os.getenv("LANG")

# TRANSLATIONS BEGIN
if currentLanguage.startswith("ar"):
    from flatsweep import lang_ar as lang
elif currentLanguage.startswith("be"):
    from flatsweep import lang_be as lang
elif currentLanguage.startswith("bg"):
    from flatsweep import lang_bg as lang
elif currentLanguage.startswith("de"):
    from flatsweep import lang_de as lang
elif currentLanguage.startswith("tr"):
    from flatsweep import lang_tr as lang
elif currentLanguage.startswith("es"):
    from flatsweep import lang_es as lang
elif currentLanguage.startswith("el"):
    from flatsweep import lang_el as lang
elif currentLanguage.startswith("ru"):
    from flatsweep import lang_ru as lang
elif currentLanguage.startswith("zh"):
    from flatsweep import lang_zh as lang
elif currentLanguage.startswith("pl"):
    from flatsweep import lang_pl as lang
elif currentLanguage.startswith("it"):
    from flatsweep import lang_it as lang
elif currentLanguage.startswith("fr"):
    from flatsweep import lang_fr as lang
elif currentLanguage.startswith("pt_BR"):
    from flatsweep import lang_pt_BR as lang
elif currentLanguage.startswith("vi"):
    from flatsweep import lang_vi as lang
elif currentLanguage.startswith("pt_PT"):
    from flatsweep import lang_pt_PT as lang
elif currentLanguage.startswith("sk"):
    from flatsweep import lang_sk as lang
elif currentLanguage.startswith("id"):
    from flatsweep import lang_id as lang
elif currentLanguage.startswith("ja"):
    from flatsweep import lang_ja as lang
else:
    from flatsweep import lang_en as lang
#TRANSLATIONS END

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, flatsweepapp, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.leftoverDataSize = 0
        self.deleteErrors = False
        self.listBoxCheckboxes = [[],[]]
        self.allCheckboxesUnchecked = False

        self.set_default_size(400, 600)
        self.set_size_request(400, 600)
        self.set_resizable(False)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.set_title("Flatsweep")
        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", "Adwaita")

        self.header = Adw.HeaderBar()
        self.header.get_style_context().add_class('flat')

        self.toolbar_view = Adw.ToolbarView()
        self.toolbar_view.add_top_bar(self.header)
        self.toolbar_view.set_content(self.scroll)

        self.set_content(self.toolbar_view)

        self.aboutButton = Gtk.Button(label="About")
        self.header.pack_start(self.aboutButton)
        self.aboutButton.connect("clicked", self.show_about)
        self.aboutButton.set_icon_name("help-about-symbolic")

        self.boxLoading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)
        self.boxCleaning = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.boxCleaned = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.boxNotFound = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.boxFirstLaunch = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.boxErrorScreen1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.loadingSpinner = Gtk.Spinner()
        self.loadingSpinner.start()
        self.loadingSpinner.set_size_request(30, 30)
        self.cleaningSpinner = Gtk.Spinner()
        self.cleaningSpinner.start()
        self.cleaningSpinner.set_size_request(30, 30)

        #Loading Window Box:
        self.loadingPage = Adw.StatusPage()
        self.loadingPage.set_icon_name("folder-symbolic")
        self.loadingPage.set_title(lang.text_calculating)
        self.loadingPage.set_child(self.loadingSpinner)
        self.boxLoading.set_margin_top(30)
        self.boxLoading.append(self.loadingPage)

        #Cleaning Window Box:
        self.cleaningPage = Adw.StatusPage()
        self.cleaningPage.set_icon_name("user-trash-symbolic")
        self.cleaningPage.set_title(lang.text_cleaning)
        self.cleaningPage.set_child(self.cleaningSpinner)
        self.boxCleaning.set_margin_top(30)
        self.boxCleaning.append(self.cleaningPage)

        #Cleaned Window Box:
        self.cleanedLabel = Gtk.Label()
        self.cleanedLabel1 = Gtk.Label()
        self.cleanedLabel1.set_text(lang.text_mbSaved)
        self.cleanedLabel1.add_css_class("title-1")
        self.cleanedLabelErrors = Gtk.Label()

        self.cleanedButtonBox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)
        self.cleanedButtonBox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)

        self.cleanedButtonBox = Gtk.Box(spacing=100)
        self.cleanedButtonIcon = Gtk.Image.new_from_icon_name("check-plain-symbolic")
        self.cleanedButtonIcon.set_pixel_size(40)
        self.cleanedButtonBox.append(self.cleanedButtonIcon)
        self.cleanedButton = Gtk.Button(child=self.cleanedButtonBox)
        self.cleanedButton.get_style_context().add_class("pill")
        self.cleanedButton.get_style_context().add_class("suggested-action")
        self.cleanedButton.connect("clicked", self.exitProgram, flatsweepapp)

        self.cleanedButtonBox2.append(self.cleanedButton)
        self.cleanedButtonBox1.append(self.cleanedButtonBox2)

        self.boxCleaned.set_margin_top(30)
        self.boxCleaned.set_spacing(30)
        self.boxCleaned.append(self.cleanedLabel)
        self.boxCleaned.append(self.cleanedLabel1)
        self.boxCleaned.append(self.cleanedLabelErrors)
        self.boxCleaned.append(self.cleanedButtonBox1)

        #No Leftovers Found Window Box:
        self.notFoundWrapped = textwrap.wrap(lang.text_notFound, width=20, break_long_words=False)
        self.notFoundLabelsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.notFoundLabel = []
        self.notFoundLineIndex = 0

        while (self.notFoundLineIndex < len(self.notFoundWrapped)):
            self.notFoundLabel.append(Gtk.Label())
            self.notFoundLabel[self.notFoundLineIndex].set_text(self.notFoundWrapped[self.notFoundLineIndex])
            self.notFoundLabel[self.notFoundLineIndex].add_css_class("title-1")
            self.notFoundLabelsBox.append(self.notFoundLabel[self.notFoundLineIndex])
            self.notFoundLineIndex += 1

        self.okButtonBox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)
        self.okButtonBox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)

        self.okButtonBox = Gtk.Box(spacing=100)
        self.okButtonIcon = Gtk.Image.new_from_icon_name("check-plain-symbolic")
        self.okButtonIcon.set_pixel_size(40)
        self.okButtonBox.append(self.okButtonIcon)
        self.okButton = Gtk.Button(child=self.okButtonBox)
        self.okButton.get_style_context().add_class("pill")
        self.okButton.get_style_context().add_class("suggested-action")
        self.okButton.connect("clicked", self.exitProgram, flatsweepapp)

        self.okButtonBox2.append(self.okButton)
        self.okButtonBox1.append(self.okButtonBox2)

        self.boxNotFound.set_margin_top(80)
        self.boxNotFound.set_spacing(50)
        self.boxNotFound.append(self.notFoundLabelsBox)
        self.boxNotFound.append(self.okButtonBox1)

        #First Launch Warning Window Box
        self.firstLaunchLabel1 = Gtk.Label()
        self.firstLaunchLabel1.set_text(lang.text_warning)
        self.firstLaunchLabel1.add_css_class("title-1")

        self.warningMessageWrapped = textwrap.wrap(lang.text_warningMessage, width=40, break_long_words=False)
        self.firstLaunchLabelsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.warningMessageLabel = []
        self.warningMessageLineIndex = 0
        while (self.warningMessageLineIndex < len(self.warningMessageWrapped)):
            self.warningMessageLabel.append(Gtk.Label())
            self.warningMessageLabel[self.warningMessageLineIndex].set_text(self.warningMessageWrapped[self.warningMessageLineIndex])
            self.warningMessageLabel[self.warningMessageLineIndex].add_css_class("title-3")
            self.firstLaunchLabelsBox.append(self.warningMessageLabel[self.warningMessageLineIndex])
            self.warningMessageLineIndex += 1

        self.firstLaunchButtonBox = Gtk.Box(spacing=100)
        self.firstLaunchButtonLabel = Gtk.Label()
        self.firstLaunchButtonLabel.set_text(lang.text_understood)
        self.firstLaunchButtonLabel.add_css_class("title-4")
        self.firstLaunchButtonBox.append(self.firstLaunchButtonLabel)

        self.firstLaunchButton = Gtk.Button(child=self.firstLaunchButtonBox)
        self.firstLaunchButton.get_style_context().add_class("pill")
        self.firstLaunchButton.get_style_context().add_class("suggested-action")
        self.firstLaunchButton.connect("clicked", self.firstLaunchDone)

        self.boxFirstLaunch.set_margin_top(80)
        self.boxFirstLaunch.set_spacing(50)

        self.firstLaunchButtonBox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)
        self.firstLaunchButtonBox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)

        self.boxFirstLaunch.append(self.firstLaunchLabel1)
        self.boxFirstLaunch.append(self.firstLaunchLabelsBox)
        self.firstLaunchButtonBox2.append(self.firstLaunchButton)
        self.firstLaunchButtonBox1.append(self.firstLaunchButtonBox2)
        self.boxFirstLaunch.append(self.firstLaunchButtonBox1)

        #Can't Find Itself Error Box:
        self.errorScreen1Label1 = Gtk.Label()
        self.errorScreen1Label1.set_text(lang.text_error)
        self.errorScreen1Label1.add_css_class("title-1")

        self.errorScreen1Label2Wrapped = textwrap.wrap(lang.text_cantFindItself, width=40, break_long_words=False)
        self.errorScreen1Label2Box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.errorScreen1Label2 = []
        self.errorScreen1Label2LineIndex = 0
        while (self.errorScreen1Label2LineIndex < len(self.errorScreen1Label2Wrapped)):
            self.errorScreen1Label2.append(Gtk.Label())
            self.errorScreen1Label2[self.errorScreen1Label2LineIndex].set_text(self.errorScreen1Label2Wrapped[self.errorScreen1Label2LineIndex])
            self.errorScreen1Label2Box.append(self.errorScreen1Label2[self.errorScreen1Label2LineIndex])
            self.errorScreen1Label2LineIndex += 1

        self.boxErrorScreen1.set_margin_top(80)
        self.boxErrorScreen1.set_spacing(50)

        self.boxErrorScreen1.append(self.errorScreen1Label1)
        self.boxErrorScreen1.append(self.errorScreen1Label2Box)

        #Main Window Box:
        self.mainLabelWrapped = textwrap.wrap(lang.text_leftoverDataAmount, width=20, break_long_words=False)
        self.mainLabelBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.mainLabel = []
        self.mainLabelLineIndex = 0
        while (self.mainLabelLineIndex < len(self.mainLabelWrapped)):
            self.mainLabel.append(Gtk.Label())
            self.mainLabel[self.mainLabelLineIndex].set_text(self.mainLabelWrapped[self.mainLabelLineIndex])
            self.mainLabel[self.mainLabelLineIndex].add_css_class("title-1")
            self.mainLabelBox.append(self.mainLabel[self.mainLabelLineIndex])
            self.mainLabelLineIndex += 1

        self.box.set_margin_top(20)
        self.box.set_spacing(30)
        self.box.append(self.mainLabelBox)

        self.boxLabelMB = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.boxLabelMB.set_spacing(-60)
        self.labelMB = Gtk.Label()
        self.labelMB.set_margin_top(-30)
        self.labelMB.set_margin_bottom(40)
        self.labelMB1 = Gtk.Label()
        self.labelMB1.set_hexpand(True)
        self.labelMB1.set_markup("<span size=\"40000\" weight=\"bold\">MB</span>")
        self.labelMB.set_hexpand(True)
        self.labelMB1.set_hexpand(True)
        self.boxLabelMB.append(self.labelMB)
        self.boxLabelMB.append(self.labelMB1)
        self.box.append(self.boxLabelMB)

        self.box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)
        self.box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)

        self.cleanbuttonBox = Gtk.Box(spacing=100)
        self.cleanbuttonLabel = Gtk.Label()
        self.cleanbuttonLabel.set_text(lang.text_clean)
        self.cleanbuttonLabel.add_css_class("title-1")
        self.cleanbuttonBox.append(self.cleanbuttonLabel)
        self.cleanbutton = Gtk.Button(child=self.cleanbuttonBox)
        self.cleanbutton.get_style_context().add_class("pill")
        self.cleanbutton.get_style_context().add_class("destructive-action")
        self.cleanbutton.connect("clicked", self.init_clean)
        self.cleanbutton.set_margin_bottom(20)

        self.box3.append(self.cleanbutton)
        self.box2.append(self.box3)
        self.box.append(self.box2)

        self.toBeCleanedBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign = Gtk.Align.CENTER, valign = Gtk.Align.CENTER)
        self.toBeCleanedBox.set_spacing(10)
        self.toBeCleanedLabelBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, valign = Gtk.Align.CENTER)
        self.toBeCleanedLabelBox.set_spacing(10)
        self.toBeCleanedLabelBox.set_margin_start(10)
        self.toBeCleanedLabelBox.set_margin_end(14)

        self.toBeCleanedLabel = Gtk.Label()
        self.toBeCleanedLabel.set_text(lang.text_toBeCleaned)
        self.toBeCleanedLabelExpandingBox = Gtk.Box()
        Gtk.Widget.set_hexpand(self.toBeCleanedLabelExpandingBox, True)
        self.toBeCleanedCheckboxAll = Gtk.CheckButton(valign=Gtk.Align.CENTER, halign=Gtk.Align.END)
        self.toBeCleanedCheckboxAll.set_active(self)
        self.toBeCleanedCheckboxAll.connect("toggled", self.toggleAllCheckboxes)
        self.toBeCleanedLabelBox.append(self.toBeCleanedLabel)
        self.toBeCleanedLabelBox.append(self.toBeCleanedLabelExpandingBox)
        self.toBeCleanedLabelBox.append(self.toBeCleanedCheckboxAll)
        self.toBeCleanedBox.append(self.toBeCleanedLabelBox)

        self.listBox = Gtk.ListBox(selection_mode = Gtk.SelectionMode.NONE)
        self.listBox.get_style_context().add_class("boxed-list")
        self.toBeCleanedBox.append(self.listBox)
        self.toBeCleanedBox.set_margin_bottom(17)
        self.box.append(self.toBeCleanedBox)

        self.connect("realize", self.init_initiate)

    def init_initiate(self, app):
        if not (os.path.exists(os.getenv("XDG_DATA_HOME") + "/firstLaunchWarningDone")):
            self.scroll.set_child(self.boxFirstLaunch)
        else:
            self.scroll.set_child(self.boxLoading)
            th = threading.Thread(target=self.initiate, args=(app))
            th.start()

    def initiate(self, app, kwargs):
        flatpakListAll = []
        if (os.path.exists("/var/lib/flatpak/app")):
            flatpakListAll += listdir("/var/lib/flatpak/app")
        if (os.path.exists(".local/share/flatpak/app")):
            flatpakListAll += listdir(".local/share/flatpak/app")
        flatpakList = set(flatpakListAll)

        if ("io.github.giantpinkrobots.flatsweep" not in flatpakList):
            self.scroll.set_child(self.boxErrorScreen1)

        else:
            varApp = []
            if (os.path.exists(os.path.join(GLib.get_home_dir(), ".var/app"))):
                varApp = [folder.name for folder in os.scandir(os.path.join(GLib.get_home_dir(), ".var/app")) if not folder.is_symlink()]

            self.leftoverData = []
            self.leftoverDataFileSizes = []

            if (varApp != []):
                for existingDataDirectory in varApp:
                    if (os.path.exists(os.path.join(os.path.join(GLib.get_home_dir(), ".var", "app", existingDataDirectory, "cache")))
                        and os.path.exists(os.path.join(os.path.join(GLib.get_home_dir(), ".var", "app", existingDataDirectory, "config")))
                        and os.path.exists(os.path.join(os.path.join(GLib.get_home_dir(), ".var", "app", existingDataDirectory, "data")))
                        and (" " not in existingDataDirectory)
                        and (existingDataDirectory not in flatpakList)):
                            dataSize = sum(foundFile.stat().st_size for foundFile in Path(os.path.join(os.path.join(GLib.get_home_dir(), ".var", "app", existingDataDirectory))).glob('**/*') if foundFile.is_file())
                            self.leftoverDataSize += dataSize
                            dataSize = int(((dataSize / 1024) / 1024) * 1.048576)
                            self.leftoverDataFileSizes.append(dataSize)
                            if (existingDataDirectory not in self.leftoverData):
                                self.leftoverData.append(existingDataDirectory)

            #Sort leftover data directories based on their size:
            if (self.leftoverData != []):
                leftoverDataZipped = sorted(zip(self.leftoverDataFileSizes, self.leftoverData), reverse=True)
                self.leftoverDataFileSizes, self.leftoverData = zip(*leftoverDataZipped)

            i = -1
            for folder in self.leftoverData:
                i += 1
                self.listBoxCheckboxes.append([])
                self.listBoxCheckboxes[i].append(Adw.ActionRow(title=folder + "  ", subtitle=str(self.leftoverDataFileSizes[i]) + "MB"))
                self.listBoxCheckboxes[i].append(Gtk.CheckButton(valign=Gtk.Align.CENTER))
                self.listBoxCheckboxes[i].append(Gtk.Button().new_from_icon_name("folder-open-symbolic"))

                self.listBoxCheckboxes[i][0].set_size_request(370, -1)
                self.listBoxCheckboxes[i][0].set_activatable(True)
                self.listBoxCheckboxes[i][0].connect("activated", self.toggleOneCheckbox, i)

                self.listBoxCheckboxes[i][1].set_active(self)
                self.listBoxCheckboxes[i][1].connect("toggled", self.ifAllCheckboxesUnchecked, app)

                self.listBoxCheckboxes[i][2].add_css_class("flat")
                self.listBoxCheckboxes[i][2].connect("clicked", partial(self.openFolder, app=app, index=i))

                self.listBoxCheckboxes[i][0].add_prefix(Gtk.Image.new_from_icon_name("flatpak-symbolic"))
                self.listBoxCheckboxes[i][0].add_suffix(self.listBoxCheckboxes[i][2])
                self.listBoxCheckboxes[i][0].add_suffix(self.listBoxCheckboxes[i][1])
                self.listBox.append(self.listBoxCheckboxes[i][0])

            self.leftoverDataSize = int(((self.leftoverDataSize / 1024) / 1024) * 1.048576)
            if (self.leftoverDataSize == 0):
                self.scroll.set_child(self.boxNotFound)
            else:
                self.labelMB.set_markup("<span size=\"70000\" weight=\"bold\">" + str(self.leftoverDataSize) + "</span>")
                self.scroll.set_child(self.box)

    def toggleOneCheckbox(self, actionrow, i):
        checkbox = self.listBoxCheckboxes[i][1]

        if checkbox.get_active():
            checkbox.set_active(False)

        else:
            checkbox.set_active(True)

        self.connect("realize", self.ifAllCheckboxesUnchecked, None)

    def toggleAllCheckboxes(self, checkbox):
        i = 0
        if checkbox.get_active():
            while (i < len(self.listBoxCheckboxes) - 2):
                self.listBoxCheckboxes[i][1].set_active(True)
                i += 1
        else:
            while (i < len(self.listBoxCheckboxes) - 2):
                self.listBoxCheckboxes[i][1].set_active(False)
                i += 1
        self.connect("realize", self.ifAllCheckboxesUnchecked, checkbox)

    def ifAllCheckboxesUnchecked(self, app, checkbox):
        allCheckboxesUnchecked = True
        allCheckboxesChecked = True
        i = 0
        while (i < len(self.listBoxCheckboxes) - 2):
            if self.listBoxCheckboxes[i][1].get_active():
                allCheckboxesUnchecked = False
            if not self.listBoxCheckboxes[i][1].get_active():
                allCheckboxesChecked = False
            i += 1
        if (allCheckboxesUnchecked == True):
            self.cleanbutton.set_sensitive(False)
            self.toBeCleanedCheckboxAll.set_active(False)
            self.allCheckboxesUnchecked = True
        else:
            self.cleanbutton.set_sensitive(True)
            self.allCheckboxesUnchecked = False
            if (allCheckboxesChecked == True):
                self.toBeCleanedCheckboxAll.set_active(True)

    def openFolder(self, row, app, index):
        os.system("xdg-open " + os.path.join(GLib.get_home_dir(), ".var", "app", self.leftoverData[index]))

    def firstLaunchDone(self, app):
        open((os.getenv("XDG_DATA_HOME") + "/firstLaunchWarningDone"), 'a').close()
        self.scroll.set_child(self.boxLoading)
        th = threading.Thread(target=self.initiate, args=(app, {}))
        th.start()

    def show_about(self, button):
        dialog = Adw.AboutDialog()
        dialog.set_application_name("Flatsweep")
        dialog.set_version(flatsweepVersion)
        dialog.set_developer_name("Giant Pink Robots!")
        dialog.set_license_type(Gtk.License(Gtk.License.MPL_2_0))
        #dialog.set_comments(lang.text_aboutDialog_Comments) # Disabling "Details" section
        dialog.set_website("https://github.com/giantpinkrobots/flatsweep")
        dialog.set_issue_url("https://github.com/giantpinkrobots/flatsweep/issues")
        dialog.set_copyright("2023 Giant Pink Robots!\n\n" + lang.text_aboutDialog_Copyright)
        dialog.set_developers(["Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots"])
        dialog.set_application_icon("io.github.giantpinkrobots.flatsweep")
        dialog.set_translator_credits("\U0001F1F8\U0001F1E6   zefr0x (@zefr0x) https://github.com/zefr0x\n\
            \U0001F1E7\U0001F1F7   Matheus Bastos (@mblithium) https://github.com/mblithium\n\
            \U0001F1F5\U0001F1F9   TickDracy (@TickDracy) https://github.com/TickDracy\n\
            \U0001F1E7\U0001F1EC   Georgi (@RacerBG) https://github.com/racerbg\n\
            \U0001F1E7\U0001F1FE   Yahor Haurylenka (@k1llo) https://github.com/k1llo\n\
            \U0001F1E8\U0001F1FF   Amerey (@Amereyeu) https://github.com/amereyeu\n\
            \U0001F1E9\U0001F1EA   saxc (@saxc) https://github.com/saxc\n\
            \U0001F1EC\U0001F1F7   Christos Georgiou Mousses (@Christosgm) https://github.com/Christosgm\n\
            \U0001F1EA\U0001F1F8   Ed M.A (@M-Duardo) https://github.com/M-Duardo\n\
            \U0001F1EB\U0001F1F7   rene-coty (@rene-coty) https://github.com/rene-coty\n\
            \U0001F1EE\U0001F1E9   ilhamfauzan (@ilhamfauzan) https://github.com/ilhamfauzan\n\
            \U0001F1EE\U0001F1F9   albanobattistella (@albanobattistella) https://github.com/albanobattistella\n\
            \U0001F1EE\U0001F1F9   Mia (@Methoko) https://github.com/Methoko\n\
            \U0001F1EF\U0001F1F5   camegone (@camegone) https://github.com/camegone\n\
            \U0001F1F5\U0001F1F1   unsolaci (@unsolaci) https://github.com/unsolaci\n\
            \U0001F1F7\U0001F1FA   Сергей Ворон (@vorons) https://github.com/vorons\n\
            \U0001F1F8\U0001F1F0   Jozef Gaal (@dodog) https://github.com/dodog\n\
            \U0001F1F9\U0001F1F7   Giant Pink Robots! (@giantpinkrobots) https://github.com/giantpinkrobots\n\
            \U0001F1FB\U0001F1F3   Xinh Nguyen (@ntxinh) https://github.com/ntxinh\n\
            \U0001F1E8\U0001F1F3   适然(Sauntor) (@sauntor) https://github.com/sauntor\n\
            \U0001F1F9\U0001F1FC   Oliver Tzeng (@olivertzeng) https://github.com/olivertzeng")
        dialog.add_other_app("io.github.giantpinkrobots.varia",
                            "Varia",
                            "Quick and efficient download manager for regular downloads, videos and torrents")
        dialog.add_other_app("io.github.giantpinkrobots.bootqt",
                            "Bootqt",
                            "Create bootable drives")

        self.set_resizable(True)
        dialog.present(self)
        self.set_resizable(False)

    def init_clean(self, app):
        if self.allCheckboxesUnchecked == False:
            self.scroll.set_child(self.boxCleaning)
            th = threading.Thread(target=self.clean, args=(app))
            th.start()

    def clean(self, app):
        cleanedData = 0
        i = -1
        for folder in self.leftoverData:
            i += 1
            if (self.listBoxCheckboxes[i][1].get_active()):
                if (os.path.join(GLib.get_home_dir(), ".var", "app", folder)):
                    try:
                        dataSize = sum(foundFile.stat().st_size for foundFile in Path(os.path.join(GLib.get_home_dir(), ".var", "app", folder)).glob('**/*') if foundFile.is_file())
                        shutil.rmtree(os.path.join(GLib.get_home_dir(), ".var", "app", folder))
                        cleanedData += dataSize
                    except:
                        self.deleteErrors = True

                if (os.path.exists(os.path.join(GLib.get_home_dir(), ".local", "share", "flatpak", "app", folder))):
                    try:
                        dataSize = sum(foundFile.stat().st_size for foundFile in Path(os.path.join(GLib.get_home_dir(), ".var", "app", folder)).glob('**/*') if foundFile.is_file())
                        shutil.rmtree(os.path.join(GLib.get_home_dir(), ".local", "share", "flatpak", "app", folder))
                        cleanedData += dataSize
                    except:
                        self.deleteErrors = True

        cleanedData = int(((cleanedData / 1024) / 1024) * 1.048576)
        self.cleanedLabel.set_markup("<span size=\"70000\" weight=\"bold\">" + str(cleanedData) + "</span>")
        if (self.deleteErrors == True):
            self.cleanedLabelErrors.set_text(lang.text_cleanedWithErrors)
            self.cleanedLabelErrors.add_css_class("title-2")
        self.scroll.set_child(self.boxCleaned)

    def exitProgram(self, app, flatsweepapp):
        flatsweepapp.quit()
        self.destroy()
        return

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app, flatsweepapp=self)
        self.win.present()

def main(version):
    app = MyApp(application_id="io.github.giantpinkrobots.flatsweep")
    app.run(sys.argv)
