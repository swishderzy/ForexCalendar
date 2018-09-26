from bs4 import BeautifulSoup
import requests
import datetime
import logging
import csv
import re

def setLogger():
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='logs_file',
                    filemode='w')
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def getEconomicCalendar(startlink,endlink):

    # write to console current status
    logging.info("Scraping data for link: {}".format(startlink))

    # get the page and make the soup
    baseURL = "https://www.forexfactory.com/"
    r = requests.get(baseURL + startlink)
    data = r.text
    soup = BeautifulSoup(data, "lxml")

    # get and parse table data, ignoring details and graph
    table = soup.find("table", class_="calendar__table")

    # do not use the ".calendar__row--grey" css selector (reserved for historical data)
    trs = table.select("tr.calendar__row.calendar_row")
    fields = ["date","time","currency","impact","event","actual","forecast","previous"]

    # some rows do not have a date (cells merged)
    curr_year = startlink[-4:]
    curr_date = ""
    curr_time = ""
    for tr in trs:

        # fields may mess up sometimes, see Tue Sep 25 2:45AM French Consumer Spending
        # in that case we append to errors.csv the date time where the error is
        try:
            for field in fields:
                data = tr.select("td.calendar__cell.calendar__{}.{}".format(field,field))[0]
                # print(data)
                if field=="date" and data.text.strip()!="":
                    curr_date = data.text.strip()
                elif field=="time" and data.text.strip()!="":
                    # time is sometimes "All Day" or "Day X" (eg. WEF Annual Meetings)
                    if data.text.strip().find("Day")!=-1:
                        curr_time = "12:00am"
                    else:
                        curr_time = data.text.strip()
                elif field=="currency":
                    currency = data.text.strip()
                elif field=="impact":
                    # when impact says "Non-Economic" on mouseover, the relevant
                    # class name is "Holiday", thus we do not use the classname
                    impact = data.find("span")["title"]
                elif field=="event":
                    event = data.text.strip()
                elif field=="actual":
                    actual = data.text.strip()
                    #state = re.findall("class=\"calendar__cell calendar__actual actual\"><span class=\"(.*)\">.*</span></td>", str(data))
                    if "better" in str(data):
                        state = "better"
                    elif "worse" in str(data):
                        state = "worse"
                    else:
                        state = "None"
                elif field=="forecast":
                    forecast = data.text.strip()
                elif field=="previous":
                    previous = data.text.strip()

            dt = datetime.datetime.strptime(",".join([curr_year,curr_date,curr_time]),
                                            "%Y,%a%b %d,%I:%M%p")
            print(",".join([str(dt),currency,impact,event,actual,forecast,previous, state]))
        except:
            with open("errors.csv","a") as f:
                csv.writer(f).writerow([curr_year,curr_date,curr_time])

    # exit recursion when last available link has reached
    if startlink==endlink:
        logging.info("Successfully retrieved data")
        return

    # get the link for the next week and follow
    follow = soup.select("a.calendar__pagination.calendar__pagination--next.next")
    follow = follow[0]["href"]
    getEconomicCalendar(follow,endlink)

if __name__ == "__main__":
    """
    Run this using the command "python `script_name`.py >> `output_name`.csv"
    """
    setLogger()
getEconomicCalendar("calendar.php?week=jan7.2007","calendar.php?week=sep23.2018")
