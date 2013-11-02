#!/usr/bin/python2
#
# MechanicalStudent
#
# This script is licensed under GPL v3.
#
# Author: Patrick Niklaus <patrick.niklaus@student.kit.edu>
#
# Simple script to automate slide downloading for the VBA software
# used inside KIT.
#
# Run: ./mechanicalstudent.py example_list
#

import mechanize
import cookielib
import getpass
import os.path
import os
import sys

URL = "https://studium.kit.edu/sites/vab/0xF27841B259D89C409E7C08B284FC3F7F"


class FakeFirefox(mechanize.Browser):
    _agent = "Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0"

    def __init__(self):
        mechanize.Browser.__init__(self)

        cj = cookielib.LWPCookieJar()
        self.set_cookiejar(cj)

        self.set_handle_equiv(True)
        self.set_handle_redirect(True)
        self.set_handle_referer(True)
        self.set_handle_robots(False)

        self.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        self.addheaders = [('User-agent', self._agent)]

class Lecture:
    _browser = None
    _vba_url = None
    _base_path = ""
    _title = ""
    _name = ""
    _pwd = ""

    def __init__(self, browser, url, name, pwd, base_path="."):
        self._browser = browser
        self._vba_url = url
        self._base_path = base_path
        self._name = name
        self._pwd = pwd

    def _login(self):
        self._browser.select_form("aspnetForm")
        user = self._browser.form.find_control("ctl00$PlaceHolderMain$Login$UserName")
        pwd = self._browser.form.find_control("ctl00$PlaceHolderMain$Login$password")
        user.value = self._name
        pwd.value = self._pwd
        self._browser.submit()

    def _detect_login_page(self, html):
        return ("ctl00$PlaceHolderMain$Login$UserName" in html)

    def get_name(self):
        return self._title

    def _set_name(self):
        self._title = self._browser.title().split(" - ")[1]

    def _get_pdf_links(self):
        self._set_name()

        # Find link to lecture slides
        to_follow = [l for l in self._browser.links() if "Vorlesungsunterlagen" in l.text]

        # extract links to pds files
        to_download = set()
        for l in to_follow:
            self._browser.follow_link(l)
            for p in self._browser.links(url_regex=".pdf"):
                to_download.add(p.absolute_url)

        return to_download

    def _download(self, url):
        fn = url.split("/")[-1]

        path = os.path.join(self._base_path, fn)
        if os.path.exists(path):
            return (False, path)

        if not os.path.exists(self._base_path):
            os.makedirs(self._base_path)

        self._browser.retrieve(url, filename=path)
        return (True, path)

    def download_slides(self):
        page = self._browser.open(self._vba_url)
        if self._detect_login_page(page.read()):
            self._login()

        links = self._get_pdf_links()

        files = []
        for link in links:
            downloaded, path = self._download(link)
            if downloaded:
                files.append(path)
        return files

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Error: Lecture list required."
        print "Format: Each line: VBA_LINK, BASE_PATH"
        sys.exit(1)

    f = open(sys.argv[1])
    lines = f.readlines()
    f.close()

    browser = FakeFirefox()

    user_name = raw_input("Username: ")
    user_pwd = getpass.getpass()

    for l in lines:
        if l.strip() == "":
            continue

        d = l.split(",")
        url = d[0]
        base_path = d[1].strip()
        print url, base_path

        l = Lecture(browser, url, user_name, user_pwd, base_path)
        files = l.download_slides()

        print "%i new slides for %s" % (len(files), l.get_name())
        for f in files:
            print f

