from bs4 import BeautifulSoup
from urllib.request import urlopen
import collections
import numpy
import time
import codecs

BASE_URL = "http://www.sherdog.com/events"
eventInfo = collections.namedtuple('Event', ['eventName', 'eventOrganizer', 'eventDate'])
fightInfo = collections.namedtuple('Fight', ['firstFighter', 'firstResult', 'secondFighter', 'secondResult'])

def make_soup(url):
	html = urlopen(url).read()
	return BeautifulSoup(html, "html.parser")

def get_card_info(soup):
	eventHeader = soup.findAll("header")[1]
	eventName = eventHeader.find("h1").string.replace(',','')
	eventName = codecs.encode(eventName, 'ascii', 'ignore')
	if eventHeader.find("h2") == None:
		eventOrganizer = "Unknown"
	else:
		eventOrganizer = eventHeader.find("h2").string.replace(',','')
	eventOrganizer = codecs.encode(eventOrganizer, 'ascii', 'ignore')
	eventDate = eventHeader.find("span", {"class": "date"}).string.replace(',','')
	thisEventInfo = numpy.asarray([eventName, eventOrganizer, eventDate])
	return thisEventInfo

def get_main_event(soup):
	eventSection = soup.find("section", {"itemprop": "subEvent"})
	if eventSection == None: return
	firstFighter = codecs.encode(eventSection.findAll("h3")[0].a.string.output_ready(formatter='utf-8'), 'ascii', 'ignore')
	if firstFighter == "Unknown Fighter": return
	secondFighter = codecs.encode(eventSection.findAll("h3")[1].a.string.output_ready(formatter='utf-8'), 'ascii', 'ignore')
	firstResult = eventSection.findAll("span", {"class": "final_result"})[0].string
	secondResult = eventSection.findAll("span", {"class": "final_result"})[1].string
	mainEvent = numpy.asarray([firstFighter, firstResult, secondFighter, secondResult])
	return mainEvent

def get_fight_table(soup, cardInfo):
	try:
		fightTable = soup.findAll("table")[1]
	except IndexError: return
	if 'resultTable' in locals():
		del resultTable
	fightRows = fightTable.findAll("tr")
	for i in range(1, len(fightRows)):
		oneFight = fightRows[i]
		firstFighter = codecs.encode(oneFight.findAll("span", {"itemprop": "name"})[0].string.output_ready(formatter='utf-8'), 'ascii', 'ignore')
		secondFighter = codecs.encode(oneFight.findAll("span", {"itemprop": "name"})[1].string.output_ready(formatter='utf-8'), 'ascii', 'ignore')
		firstResult = oneFight.findAll("span", {"class": "final_result"})[0].string
		secondResult = oneFight.findAll("span", {"class": "final_result"})[1].string
		fightResults = numpy.asarray([firstFighter, firstResult, secondFighter, secondResult])
		fightResults = numpy.concatenate([cardInfo, fightResults])
		if 'resultTable' in locals():
			resultTable = numpy.vstack([resultTable, fightResults])
		else:
			resultTable = fightResults
	return resultTable

def scrape_web_page(event_url):
	soup = make_soup(event_url)
	cardInfo = get_card_info(soup)
	if cardInfo == None: return
	mainEvent = get_main_event(soup)
	if mainEvent == None: return
	pageTable = numpy.concatenate([cardInfo, mainEvent])
	newFight = get_fight_table(soup, cardInfo)
	if newFight != None:
		pageTable = numpy.vstack([pageTable, newFight])
	return pageTable

def scrape_event_page(event_url):
	soup = make_soup(event_url)
	if 'allFightResults' in locals():
		del allFightResults
	linkList = soup.findAll("a", {"itemprop": "url"})
	for i in range(0, len(linkList)):
	#for i in range(15, len(linkList)):
		pageResults = scrape_web_page(BASE_URL + linkList[i].get("href"))
		if pageResults != None:
			if 'allFightResults' in locals():
				allFightResults = numpy.vstack([allFightResults, pageResults])
			else:
				allFightResults = pageResults
	return allFightResults

def loop_event_pages(fP,lP):
	if 'finalResults' in locals(): del finalResults
	for i in range(fP, lP+1):
		#time.sleep(1.1)
		eventPageURL = BASE_URL + "/recent/" + str(i) +"-page"
		eventPageScraped = scrape_event_page(eventPageURL)
		if 'finalResults' in locals():
			finalResults = numpy.vstack([finalResults, eventPageScraped])
		else:
			finalResults = eventPageScraped
		print(str(time.time()) + " " + eventPageURL)
	return finalResults

for i in range(81, 250, 5):
	csvName = "MMA_raw_" + str(i) + "_" + str(i+4) + ".csv"
	numpy.savetxt(csvName, loop_event_pages(i,i+4), fmt="%s", delimiter=",")
