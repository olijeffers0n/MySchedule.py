import requests
import datetime
import bs4
import pybase64
from typing import List
from lxml import etree
import re
from .structures import *


DAYS = {0: "Mon.", 1: "Tues.", 2: "Weds.", 3: "Thurs.", 4: "Fri.", 5: "Sat.", 6: "Sun."}


class ScheduleAPI:

    def __init__(self, username, password):
        self.username: str = username
        self.password: str = password
        self.auth_token: str = None
        self.data: dict = None
        self.session: requests.Session = requests.session()

    @staticmethod
    def get_week_code_for_date(date: datetime) -> str:
        """
        :param date: The date to get the week code for
        :return: The week code for the given date
        """
        iso = date.isocalendar()
        return "7" + str(iso[0])[2:] + str(iso[1])

    def get_current_week(self) -> int:
        req = self.session.get("https://mcduk.reflexisinc.co.uk/RWS4/ess/ess_emp_schedule.jsp?authToken=" + self.auth_token)
        data = str(req.content)
        index = data.index("setGenShiftId")

        return int(data[index + 14:index + data[index:].index(")")])

    @staticmethod
    def generate_date(date_string: str) -> datetime:
        return datetime.strptime(str(date_string), "%Y%m%d")

    @staticmethod
    def time_from_number(number):
        minutes = str(number % 60)
        return f"{number // 60}:{minutes if len(minutes) == 2 else minutes + '0'}"

    def _create_form(self):
        data = self.session.get("https://mcduk.reflexisinc.co.uk/kernel/views/authenticate/W/MCDUK.view")
        # Use the lxml parser to parse the html
        html = bs4.BeautifulSoup(data.content, "html.parser")
        other_stuff = html.find_all("div", {"id": "login-content"})[0].find_all("input", {"type": "hidden"})

        divs = []

        for div in html.find_all("div", {"id": "primaryAuthenticationContainer"})[0].find_all("div"):

            clazz = div.get("class")[0] if div.get("class") is not None else ""
            ids = div.get("id")

            if clazz in ["access-username", "access-password"] or \
                    ids in ["useridBlankErrorMessage", "passwordBlankErrorMessage"]:
                continue

            divs.append(div)

        username_div, password_div = divs

        params = {
            "selectedLocale": "en_GB",
            "hidden": "",
            "secureFormFields": True,
            username_div.find_all("input")[0].get("name"): self.username,
            password_div.find_all("input")[1].get("name"): pybase64.encodebytes(self.password.encode("utf-8")).decode(
                "utf-8")
        }

        for div in other_stuff:
            params[div.get("name")] = div.get("value")

        login_req = self.session.post("https://mcduk.reflexisinc.co.uk/kernel/views/validateuserlogin.view",
                                      data=params)

        return login_req.content

    def _create_session(self, create_form_html):
        html = bs4.BeautifulSoup(create_form_html, "html.parser")
        body = html.find_all("body")[0]
        inputs = body.find_all("input", {"type": "hidden"})

        data = {section.get("name"): section.get("value") for section in inputs}
        self.data = data
        self.session.post("https://mcduk.reflexisinc.co.uk/kernel/auth/createLocalSession.rest", data=data)

        return data["authToken"]

    def _get_all_data(self):
        data = self.session.post("https://mcduk.reflexisinc.co.uk/MYWORK/systemAction.htm", data={
            "localeCode": self.data["localeCode"],
            "authToken": self.auth_token,
            "expiresOn": self.data["expiresOn"],
            "operation": "logUserIn",
            "domainId": self.data["domainId"],
            "X-reflexis-header-X": self.data["X-reflexis-header-X"],
        })

        html = bs4.BeautifulSoup(data.content, "html.parser").decode()

        start = html.find("var globalObject = function globalConstants(){")
        end = html[start:].find("return{")

        variables = {}

        for line in html[start+46:end+len(html[:start])].split("\n"):
            if line.strip() == "":
                continue
            new_line = line.strip().replace("var ", "").replace(";", "")
            variables[new_line.split("=")[0].strip()] = new_line.split("=")[1].strip().replace("'", "")

        self.data.update(variables)

    def login(self) -> None:
        create_form_html = self._create_form()
        self.auth_token = self._create_session(create_form_html)
        self._get_all_data()

    def get_shifts_for_week(self, week_code: int) -> List[Shift]:
        """
        :param week_code: The week code to get the shifts for
        :return: A list of shifts for the given week code
        """
        shifts = []

        if self.data is None:
            raise Exception("You must login before you can get shifts")

        self.session.get("https://mcduk.reflexisinc.co.uk/RWS4/ess/ess_emp_schedule.jsp?authToken=" + self.auth_token)
        req = self.session.get(f"https://mcduk.reflexisinc.co.uk/RWS4/controller/ess/map/{self.data['storeId']}/"
                               f"{week_code}"
                               f"/requestswithshiftsdata.json?authToken={self.auth_token}")

        if req.status_code != 200:
            raise Exception("Failed to get shifts")

        for date, data in req.json().items():
            if not data:
                continue

            date_obj = self.generate_date(date)

            shifts.append(Shift(date_obj, self.time_from_number(data[0]["startTime"]),
                                self.time_from_number(data[0]["endTime"]),
                                self.time_from_number(data[0]["duration"]), data))

        return shifts

    def get_shifts_for_date(self, date: datetime.date) -> List[Shift]:
        """
        :param date: The date to get the shifts for
        :return: A list of shifts for the given date
        """
        return self.get_shifts_for_week(int(self.get_week_code_for_date(date)))

    
    @staticmethod
    def extract_time(cdata):
        """
        :param cdata: The CDATA content to extract the time from
        :return: The time extracted from the CDATA content
        """

        time_match = re.search(r"\d{2}:\d{2}", cdata)
        if time_match:
            return time_match.group()
        return None

    def get_timecard(self):
        """
        :param week_code: The week code to get the timecard for
        :return: A timecard for the given week code
        """

        # Make a request to the timecard page
        tc_request = self.session.post("https://mcduk.reflexisinc.co.uk/RWS4/rta/tcard.jsp", data={
            "reqType": "STAFF",
            "authToken": self.auth_token,
        })
    
        # If the request failed, raise an exception
        if tc_request.status_code != 200:
            raise Exception("Failed to get timecard")

        # Use BS4 to parse the HTML
        parsed_html = bs4.BeautifulSoup(tc_request.content, "html.parser").decode()

        # Extract the XML content from the JavaScript variable
        punch_variable_match = re.search(r'punchXMLLoad\s*=\s*\'(.*?)\';', parsed_html, re.DOTALL)
        punch_xml_string = punch_variable_match.group(1)

        # Remove all backslashes from the XML content
        punch_xml_string = punch_xml_string.replace("\\", "")

        # Remove XML declaration
        punch_xml_string = punch_xml_string.replace('<?xml version="1.0" encoding="UTF-8"?>', "")

        # Parse the XML content
        tree = etree.fromstring(punch_xml_string)

        # Extract the HH:MM and punch type from each CDATA content and store in a list of dictionaries
        data_dict = {}
        date = None

        # Loop through each row in the XML
        for row in tree.xpath("//row"):
            date_nodes = row.xpath("cell[1]/text()")
            time_nodes = row.xpath("cell[2]/text()")
            punch_type_nodes = row.xpath("cell[3]/text()")

            # Check if date is present, update the date variable and add a new entry to the data dictionary
            if date_nodes:
                date = date_nodes[0]
                data_dict[date] = {"punches": []}

            # Check if time and punch is present
            if time_nodes and punch_type_nodes:
                # Extract the time and punch type from the CDATA content
                time = self.extract_time(time_nodes[0])

                punch_type_match = re.search(r'src="/RWS4/images/TC(.*?)\.png"',  punch_type_nodes[0])
                punch_type = punch_type_match.group(1) if punch_type_match else None

                # Add the time and punch type as a new entry
                data_dict[date]["punches"].append({"time": time, "punch_type": punch_type})
        return data_dict