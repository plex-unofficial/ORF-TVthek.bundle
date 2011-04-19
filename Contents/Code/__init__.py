#!/usr/bin/python
# -*- coding: utf-8 -*-
# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
# from lxml import etree

####################################################################################################

VIDEO_PREFIX = "/video/orftvthek"
URL = "http://tvthek.orf.at"
URLprograms = "http://tvthek.orf.at/programs"
SEARCH_URL = 'http://tvthek.orf.at/search?q=%s'
DEBUG = False
#CACHE_TIME = 3600

NAME = L('Title')
ART = 'tvthek_bg.jpg'
ICON = 'icon-default.jpg'

####################################################################################################
def Start():
	Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('VideoTitle'), ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)
		
def CreatePrefs():
	Prefs.Add(id='orf1', type='bool', default=True, label='ORF1')
	Prefs.Add(id='orf2', type='bool', default=True, label='ORF2')

def ValidatePrefs():
	orf1 = Prefs.Get('orf1')
	orf2 = Prefs.Get('orf2')

def MainMenu():
	dir = MediaContainer(viewGroup="InfoList")

	htmlPage = XML.ElementFromURL(URL, isHTML=True, cacheTime=None)

	categoryItems = htmlPage.xpath('//div[@id="content"]//div[contains(@class, "row")][1]//div[@class="content"]')
	CategoryMenu(dir, categoryItems)
		
	menuItems = htmlPage.xpath('//ul[@id="menu"]/li')
	for menuItem in menuItems:
		title = menuItem.xpath('./a/span')[0].text
		title = title.lstrip()
		subtitle = menuItem.xpath('./a')[0].get("title")
		#PMS.Log("Title: " + title + " | Subtitle: " + subtitle)
		if subtitle.find("Startseite"):
			subPageURL = URL+menuItem.xpath('./a')[0].get("href")
			dir.Append(Function(DirectoryItem(SubMenu, title=title, subtitle = subtitle), subPageURL=subPageURL))

	SearchMenuItem(dir)
	#dir.Append(PrefsItem("Preferences..."))

	return dir

def SubMenu(sender, subPageURL):
	#global categoryItems
		
	dir = MediaContainer(viewGroup="InfoList")
	dir.title2 = sender.itemTitle

	PMS.Log("Item: " + sender.itemTitle + " (" + subPageURL)

	htmlPage = XML.ElementFromURL(subPageURL, isHTML=True, cacheTime=None)
	categoryItems = htmlPage.xpath('//div[@id="content"]//div[contains(@class, "row")]//div[@class="content"]')
	
	if len(categoryItems) == 0 and (sender.itemTitle.rstrip() =="Sendung verpasst?"):
		missedItems = htmlPage.xpath('//form[@id="orf_check"]//li[not(@class="channels")]//button')
		missedItems.reverse()
		#PMS.Log("Missed Items length: " + str(len(missedItems)))
		MissedItems(dir, missedItems, subPageURL)
		
	CategoryMenu(dir, categoryItems, sender.itemTitle, sub=True)
		
	if (len(dir) == 0) and (sender.itemTitle.rstrip() == "Live"):
		return MessageContainer("Zur Zeit kein Live Stream ...", "Momentan ist kein Live Stream verfuegbar")
		
	if (len(dir) == 0) and (sender.itemTitle.rstrip() == "Sendung verpasst?"):
		return MessageContainer(sender.itemTitle.rstrip(), "noch nicht implementiert ...")

	else:
		return dir

def CategoryMenu(dir, categoryItems, item=None, sub=False):
	#global categoryItems
	global catItems, subcatItems
	

	PMS.Log("CategoryMenu Item: " + str(item))
	
	if sub:
		subcatItems = categoryItems
	else:
		catItems = categoryItems
				
	PMS.Log("Nr. of Menu Items: " + str(len(categoryItems)))
	
	for itemix, categoryItem in enumerate(categoryItems):
		category = getCategoryDetails(categoryItem)
		

		if item and (item.rstrip() == "Live"):
			PMS.Log("(CategoryMenu)Item: " + item)
			PMS.Log("Item: " + category.title + " : " + category.subtitle)
			try:
				asxFile = categoryItem.xpath('//object[@id="WmPlayerObject"]/param[@name="URL"]')[0].get("value")
			except:
				break
			try:
				showThumb = categoryItem.xpath(".//img")[0].get("src")
			except:
				showThumb = None		
			try:
				showDateTime = categoryItem.xpath('.//span[@class="desc_time genre"]')[0].text
			except:
				showDateTime = " "
			try:
				showDesc = categoryItem.xpath('.//span[@class="desc"]')[0].text
			except:
				showDesc = " "
			dir.Append(VideoItem(asxFile, category.title, subtitle=category.subtitle, summary=showDesc, duration='', thumb=showThumb))			
			break
		else:
			#strCategoryItem = XML.StringFromElement(categoryItem, method="html")
			#PMS.Log("categoryItem 'stringed' : "+strCategoryItem)
			dir.Append(Function(category, itemix=itemix, sub=sub))
			#dir.Append(Function(DirectoryItem(ShowsInCategory, title=category.title, subtitle=category.subtitle), item=strCategoryItem))
			#PMS.Log("categoryItem 'stringed' : "+strCategoryItem)
			PMS.Log("Item: " + category.title + " : " + category.subtitle)
	return dir

def ShowsInCategory(sender, itemix, sub):
	#global categoryItems
	
	if sub:
		categoryItem = subcatItems[itemix]
	else:
		categoryItem = catItems[itemix]
	
	#PMS.Log("categoryItem 'stringed' : "+item)
	dir = MediaContainer(viewGroup="InfoList")
	dir.title2 = sender.itemTitle
	
	#for categoryItem in categoryItems:
	#	category = getCategoryDetails(categoryItem)	
	#	if (sender.itemTitle == category.title):
	#		listVideoItems(dir, categoryItem)
	#categoryItem = XML.ElementFromString(item)
	listVideoItems(dir, categoryItem)
	
	return dir

def getCategoryDetails(item):
	try:
		catTitle = item.xpath("../h3/span")[0].text
	except:
		#catTitle = item.xpath("../h3/a")[0].get("title")
		catTitle = item.xpath("../h3/a")[0].text

	try:
		catSubtitle = item.xpath("../h3/span")[0].text
	except:
		catSubtitle = item.xpath("../h3/a")[0].get("title")
	
	# if type(catTitle) is types.NoneType:
	if (not catTitle):
		#if subPageURL == URL+"/":
			catTitle = "Meldungsübersicht"
			catSubtitle = "Aktuelle Beiträge"
	
	category = DirectoryItem(ShowsInCategory, None)
	category.title = catTitle.lstrip()
	category.subtitle = catSubtitle
	
	return category

def listVideoItems(dir, item):
	try:
		moreShows = item.xpath('../h3/a[@class="more"]')[0].get('href')
	except:
		moreShows = " "
	
	moreShows = str(moreShows)
	if moreShows == " ":
		PMS.Log("**************** listVideoItems *************")	
	
		shows = item.xpath('.//li/a')

		for show in shows:
			makeVideoItems(dir, show)			
	else:
		htmlPage = XML.ElementFromURL(URL+moreShows, isHTML=True, cacheTime=None)
		menuItems = htmlPage.xpath('//div[@id="content"]//div[contains(@class, "row")]//div[@class="content"]')
		#catTitle = GetCatTitle(menuItem, URL+moreShows)
		PMS.Log("**********listVideoItems - more shows *************")		
		listVideoItems(dir, menuItems.pop())
		#PMS.Log(catTitle + " - Nr. of menuItems: " + str(len(menuItems)))
	return dir

def makeVideoItems(dir, show):
	#global segments
	showTitle = show.xpath('.//strong')[0].text
	
	if (dir.title2 == "Meldungsübersicht") or (not showTitle):
		showTitle = show.xpath('.//strong/span')[0].text
	
	showTitle = showTitle.lstrip()
	
	showHref = show.get("href")
	showThumb = show.xpath(".//img")[0].get("src")
		
	try:
		showDateTime = show.xpath('.//span[@class="desc_time genre"]')[0].text
	except:
		showDateTime = " "
	try:
		showDesc = show.xpath('.//span[@class="desc"]')[0].text
	except:
		showDesc = " "

	#asxContainer = XML.ElementFromURL(URL+showHref, isHTML=True)
	#asxFile = URL+asxContainer.xpath('//object[@id="WmPlayerObject"]/param[@name="URL"]')[0].get("value")
	#PMS.Log("asxFile: "+asxFile)
	# the following plays the Show (with all its subsegments automatically ....)
	# dir.Append(VideoItem(asxFile, showTitle, subtitle=showDateTime, summary=showDesc, duration='', thumb=showThumb))
	# the following inserts a menu that lets the user select to play all segments automatically or select indivudual segments
	dom = XML.ElementFromURL(URL+showHref, isHTML=True, cacheTime=None)
	asxFile = URL+dom.xpath('//object[@id="WmPlayerObject"]/param[@name="URL"]')[0].get("value")
	segments = dom.xpath('//div[@id="segment-tab"]//ul[@class="vods"]/li/a')
	nrSegments = len(segments)
	if nrSegments > 1:
		dir.Append(Function(DirectoryItem(SubSegments, title=showTitle, subtitle = showDateTime, summary=showDesc, thumb=showThumb), showURL=URL+showHref, subTitle=showDateTime, summary=showDesc, thumb=showThumb))
	else:
		dir.Append(VideoItem(asxFile, showTitle, subtitle=showDateTime, summary=showDesc, duration='', thumb=showThumb))

def SubSegments(sender, showURL, subTitle, summary, thumb):
	#global segments

	dir = MediaContainer(viewGroup="InfoList")
	dir.title2 = sender.itemTitle

	dom = XML.ElementFromURL(showURL, isHTML=True, cacheTime=None)
	asxFile = URL+dom.xpath('//object[@id="WmPlayerObject"]/param[@name="URL"]')[0].get("value")
	segments = dom.xpath('//div[@id="segment-tab"]//ul[@class="vods"]/li/a')
	nrSegments = len(segments)
	if nrSegments > 1:
		dir.Append(VideoItem(asxFile, "Alle Beitraege abspielen", subtitle=sender.itemTitle+" - "+subTitle, summary=summary, duration='', thumb=thumb))
		for ix, segment in enumerate(segments):
			asxURL=segment.get("href")
			dom = XML.ElementFromURL(URL+asxURL, isHTML=True, cacheTime=None)
			asxFile = URL+dom.xpath('//object[@id="WmPlayerObject"]/param[@name="URL"]')[0].get("value")
			sumXpath='//li[@id="playlist_entry_'+str(ix+1)+'"]/p'
			summary=dom.xpath('//li[@id="playlist_entry_'+str(ix+1)+'"]/p')[0].text
			title=segment.get("title")
			duration=segment.xpath('.//span[@class="duration"]')[0].text
			dir.Append(VideoItem(asxFile, title+" " +duration, subtitle=sender.itemTitle+ " - "+subTitle, summary=summary, duration='', thumb=thumb))
	#else:
	#	#dir.replaceParent = True
	#	dir.Append(VideoItem(asxFile, sender.itemTitle, subtitle=subTitle, summary=summary, duration='', thumb=thumb))
	return dir	

def MissedItems(dir, missedItems, subPageURL):
	if missedItems:
		
		for item in missedItems:
			url = "/last/" + item.get("value")
			subtitle = item.get("title")
			title = item.text.lstrip()
			PMS.Log("Missed Item: " + title + " : " + subtitle + "(" + subPageURL+url + ")")
			dir.Append(Function(DirectoryItem(MissedItemsDay, title=title, subtitle = subtitle), subPageURL=subPageURL+url))
		
	return dir

def MissedItemsDay(sender, subPageURL):
	dir = MediaContainer(viewGroup="InfoList")
	dir.title2 = "Verpasste Sendungen " + sender.itemTitle
	
	PMS.Log("Missed Items URL: " + subPageURL)
	htmlPage = XML.ElementFromURL(subPageURL, isHTML=True, cacheTime=None)
	shows = htmlPage.xpath('//table[@id="broadcasts"]/tbody/tr')
	
	PMS.Log("Missed Shows: " + str(len(shows)))
	if (not shows):
		#message = htmlPage.xpath('//div[@class="hint404"]/p')[0]
		return MessageContainer(sender.itemTitle, "Für diesen Tag sind noch keine Sendungen verfügbar")
	
	for show in shows:
		channel = show.xpath('./td[@class="channel"]/img')[0].get("alt")[:5]
		time = show.xpath('./td[@class="time"]')[0].text
		thumb = show.xpath('./td[@class="episode"]//img')[0].get("src")
		showinfo = show.xpath('./td[@class="info"]')[0]
		url = showinfo.xpath('./h4/a')[0].get("href")
		title = showinfo.xpath('./h4/a')[0].text
		duration = showinfo.xpath('./p[@class="duration"]')[0].text
		subtitle=channel + ", " + time + " " + duration
		summary = showinfo.xpath('./p[@class="descr"]')[0].text
		dir.Append(Function(DirectoryItem(SubSegments, title=title, subtitle=subtitle, summary=summary, thumb=thumb), showURL=URL+url, subTitle=subtitle, summary=summary, thumb=thumb))
		
		
	return dir

def SearchMenuItem(dir):
	dir.Append(
		Function(
			InputDirectoryItem(
				SearchResults,
				"Suche ...",
				"... und finde",
				summary = "... und finde",
				thumb=R(ICON),
				art=R(ART)
			)
		)
	)
	return dir

def SearchResults(sender,query=None):
	return MessageContainer(
		"Suche nach: " + query + " ...",
		"... [noch] nicht implementiert ..."
	)
	
#def GetCatTitle(item, subPageURL):
#	
#	try:
#		catTitle = item.xpath("../h3/span")[0].text
#	except:
#		catTitle = item.xpath("../h3/a")[0].get("title")
#		#catTitle = item.xpath("../h3/a")[0].text
#		
#	if type(catTitle) is types.NoneType:
#		if subPageURL == URL+"/":
#			catTitle = "Meldungsübersicht"
#	PMS.Log("def GetCatTitle: catTitle: " + str(catTitle) + " URL: " + subPageURL)
#	return catTitle

#def listVideoItems(dir, itemTitle, url):
#	PMS.Log("**************** listVideoItems *************")
#	global menuItems, htmlPage
#	for menuItem in menuItems:
#		#PMS.Log("URL: %s" % url)
#		#catTitle = GetCatTitle(menuItem, url)
#		category = getCategoryDetails(menuItem)
#		catTitle = category.title
#	
#		PMS.Log(catTitle+" - "+itemTitle)
#		if catTitle == itemTitle:
#			try:
#				moreShows = menuItem.xpath('../h3/a[@class="more"]')[0].get('href')
#			except:
#				moreShows = " "
#			
#			moreShows = str(moreShows)
#			PMS.Log("moreShows: %s" % moreShows)
#			if moreShows == " ":
#			
#				shows = menuItem.xpath('.//li/a')
#		
#				for show in shows:
#					
#					showTitle = show.xpath('.//strong')[0].text
#					
#					if (catTitle == 'Meldungsübersicht') or (not showTitle):
#						showTitle = show.xpath('.//strong/span')[0].text
#					
#					showHref = show.get("href")
#					showThumb = show.xpath(".//img")[0].get("src")
#					
#					try:
#						showDateTime = show.xpath('.//span[@class="desc_time genre"]')[0].text
#					except:
#						showDateTime = " "
#					try:
#						showDesc = show.xpath('.//span[@class="desc"]')[0].text
#					except:
#						showDesc = " "
#
#					asxContainer = XML.ElementFromURL(URL+showHref, isHTML=True)
#					asxFile = URL+asxContainer.xpath('//object[@id="WmPlayerObject"]/param[@name="URL"]')[0].get("value")
#					#PMS.Log("asxFile: "+asxFile)
#					dir.Append(VideoItem(asxFile, showTitle, subtitle=showDateTime, summary=showDesc, duration='', thumb=showThumb))
#			else:
#				htmlPage = XML.ElementFromURL(URL+moreShows, isHTML=True)
#				menuItems = htmlPage.xpath('//div[@id="content"]//div[contains(@class, "row")]//div[@class="content"]')
#				catTitle = GetCatTitle(menuItem, URL+moreShows)
#				listVideoItems(dir, catTitle, URL+moreShows)
#				PMS.Log("**********listVideoItems - more shows *************")
#				PMS.Log(catTitle + " - Nr. of menuItems: " + str(len(menuItems)))
#	return dir