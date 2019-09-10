#!/usr/bin/python
# -*- coding: utf-8 -*-

# for localized messages     
from . import _

import owibranding

from Screens.Screen import Screen
from plugin import skin_path, cfg, playlist_file

from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.Sources.List import List
from Components.config import *
from Components.ConfigList import *
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox

from collections import OrderedDict
from datetime import datetime
from Tools.LoadPixmap import LoadPixmap
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER

import os
import json
import buildbouquet, playlists
import jediglobals as jglob
import globalfunctions as jfunc
import downloads

class JediMakerXtream_Bouquets(ConfigListScreen, Screen):

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		
		skin = skin_path + 'jmx_settings.xml'
		
		self.dreamos = False
		
		try:
			from boxbranding import getImageDistro, getImageVersion, getOEVersion
		except:
			self.dreamos = True
			if owibranding.getMachineBrand() == "Dream Multimedia" or owibranding.getOEVersion() == "OE 2.2":
				skin = skin_path + 'DreamOS/jmx_settings.xml'

		with open(skin, 'r') as f:
			self.skin = f.read()
						
		self.setup_title = _('Bouquets Settings')
		
		self.onChangedEntry = []
		
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
		
		self.loaded = False
		
				
		self['information'] = Label('')
		
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Continue'))
		
		self['VirtualKB'].setEnabled(False)
		self['HelpWindow'] = Pixmap()
		self['VKeyIcon'] = Pixmap()
		self['HelpWindow'].hide()
		self['VKeyIcon'].hide()
		self['lab1'] = Label(_('Loading data... Please wait...'))

		self['actions'] = ActionMap(['SetupActions'], {
		 'save': self.save,
		 'cancel': self.cancel
		 }, -2)
		 
		self.pause = 100 
		
		address = jglob.current_playlist['playlist_info']['address']
		self.playlisttype = jglob.current_playlist['playlist_info']['playlisttype']
		
		#defaults
		if cfg.bouquet_id.value:
			jglob.bouquet_id = cfg.bouquet_id.value
		else: 
			jglob.bouquet_id = 666

		# if xtream or external
		if self.playlisttype != 'local':
			protocol = jglob.current_playlist['playlist_info']['protocol']
			domain = jglob.current_playlist['playlist_info']['domain']
			port = str(jglob.current_playlist['playlist_info']['port'])   
			host = str(protocol) + str(domain) + ':' + str(port) + '/' 
			jglob.name = domain
		else:
			jglob.name = address
			
		if self.playlisttype == 'xtream':
			username = jglob.current_playlist['playlist_info']['username']
			password = jglob.current_playlist['playlist_info']['password']
			player_api = str(host) + 'player_api.php?username=' + str(username) + '&password=' + str(password)
			self.enigma_api = str(host) + 'enigma2.php?username=' + str(username) + '&password=' + str(password)
			jglob.xmltv_address = str(host) + 'xmltv.php?username=' + str(username) + '&password=' + str(password) 
			
			self.LiveCategoriesUrl = player_api + '&action=get_live_categories'
			self.VodCategoriesUrl = player_api + '&action=get_vod_categories'
			self.SeriesCategoriesUrl = player_api + '&action=get_series_categories'
		
			self.LiveStreamsUrl = player_api + '&action=get_live_streams'
			self.VodStreamsUrl = player_api + '&action=get_vod_streams'
			self.SeriesUrl = player_api + '&action=get_series'
			
			jglob.epg_provider = True
		else:
			jglob.epg_provider = False
			

		jglob.old_name = jglob.name
		jglob.categories = []
		

		if 'bouquet_info' in jglob.current_playlist and jglob.current_playlist['bouquet_info'] != {}:
			jfunc.readbouquetdata()
		else:
			jglob.live_type = '4097'
			jglob.vod_type = '4097'
			jglob.vod_order = 'original'

			jglob.epg_rytec_uk = False
			jglob.epg_swap_names = False
			jglob.epg_force_rytec_uk = False

			jglob.live = True
			jglob.vod = False
			jglob.series = False
			jglob.prefix_name = True
			
		if self.playlisttype == 'xtream':
			
			# download enigma2.php to get categories    
			self.timer = eTimer()
			self.timer.start(self.pause, 1)
			try:
				self.timer_conn = self.timer.timeout.connect(self.downloadEnigma2Data)
			except:
				self.timer.callback.append(self.downloadEnigma2Data)
				
		else:
			self.createConfig()
			self.createSetup()
		
		self.onLayoutFinish.append(self.__layoutFinished)
		
		if self.setInfo not in self['config'].onSelectionChanged:
			self['config'].onSelectionChanged.append(self.setInfo)


	def __layoutFinished(self):
		self.setTitle(self.setup_title)


	def downloadEnigma2Data(self):
		#downloads.downloadenigma2categories(self.enigma_api)
		
		if self.playlisttype == 'xtream':
			downloads.downloadlivecategories(self.LiveCategoriesUrl)
			downloads.downloadvodcategories(self.VodCategoriesUrl)
			downloads.downloadseriescategories(self.SeriesCategoriesUrl)
		
		self.createConfig()
		self.createSetup()


	def createConfig(self):
		self['lab1'].setText('')
		self.NameCfg = NoSave(ConfigText(default=jglob.name, fixed_size=False))
		
		self.PrefixNameCfg = NoSave(ConfigYesNo(default=jglob.prefix_name))
		
		self.LiveCategoriesCfg = NoSave(ConfigYesNo(default=jglob.live))
		self.VodCategoriesCfg = NoSave(ConfigYesNo(default=jglob.vod))
		self.SeriesCategoriesCfg = NoSave(ConfigYesNo(default=jglob.series))
		
		self.XmltvCfg = NoSave(ConfigText(default=jglob.xmltv_address, fixed_size=False))
		
		self.VodOrderCfg = NoSave(ConfigSelection(default='alphabetical', choices=[('original', _('Original Order')), ('alphabetical', _('A-Z')), ('date', _('Newest First')), ('date2', _('Oldest First'))]))
		
		self.EpgProviderCfg = NoSave(ConfigEnableDisable(default=jglob.epg_provider))
		self.EpgRytecUKCfg = NoSave(ConfigEnableDisable(default=jglob.epg_rytec_uk))
		self.EpgSwapNamesCfg = NoSave(ConfigEnableDisable(default=jglob.epg_swap_names))
		self.ForceRytecUKCfg = NoSave(ConfigEnableDisable(default=jglob.epg_force_rytec_uk))
		
		if os.path.isdir('/usr/lib/enigma2/python/Plugins/SystemPlugins/ServiceApp'):
			self.LiveTypeCfg = NoSave(ConfigSelection(default=jglob.live_type, choices=[
			 ('1', _('DVB(1)')),
			 ('4097', _('IPTV(4097)')), 
			 ('5001', _('GStreamer(5001)')), 
			 ('5002', 'ExtPlayer(5002)')]))
			self.VodTypeCfg = NoSave(ConfigSelection(default=jglob.vod_type, choices=[
			 ('1', _('DVB(1)')), 
			 ('4097', _('IPTV(4097)')), 
			 ('5001', _('GStreamer(5001)')), 
			 ('5002', 'ExtPlayer(5002)')]))
		else:
			self.LiveTypeCfg = NoSave(ConfigSelection(default=jglob.live_type, choices=[('1', _('DVB(1)')), ('4097', _('IPTV(4097)'))]))
			self.VodTypeCfg = NoSave(ConfigSelection(default=jglob.vod_type, choices=[('1', _('DVB(1)')), ('4097', _('IPTV(4097)'))]))


	def createSetup(self):
		
		
		self.list = []
		self.list.append(getConfigListEntry(_('Bouquet name'), self.NameCfg))
		
		self.list.append(getConfigListEntry(_('Use name as bouquet prefix'), self.PrefixNameCfg))
		
		if self.playlisttype == 'xtream':
			
			if jglob.haslive:
				self.list.append(getConfigListEntry(_('Live categories'), self.LiveCategoriesCfg))
				
			if self.LiveCategoriesCfg.value == True:
				self.list.append(getConfigListEntry(_('Stream type for Live'), self.LiveTypeCfg))
		   
			if jglob.hasvod:
				self.list.append(getConfigListEntry(_('VOD categories'), self.VodCategoriesCfg))
				
			if jglob.hasseries:
				self.list.append(getConfigListEntry(_('Series categories'), self.SeriesCategoriesCfg))
			
			if self.VodCategoriesCfg.value == True or self.SeriesCategoriesCfg.value == True:
				self.list.append(getConfigListEntry(_('Stream type for VOD/SERIES'), self.VodTypeCfg))
			   
			if self.VodCategoriesCfg.value == True:
				self.list.append(getConfigListEntry(_('VOD bouquet order'), self.VodOrderCfg))
		 
			if self.LiveCategoriesCfg.value == True and jglob.has_epg_importer: 
				self.list.append(getConfigListEntry(_('Use your provider EPG'), self.EpgProviderCfg))
			
			
			if self.LiveCategoriesCfg.value == True and jglob.has_epg_importer: 
				self.list.append(getConfigListEntry(_('Use Rytec UK EPG'), self.EpgRytecUKCfg))

			if self.EpgRytecUKCfg.value == True:
				self.list.append(getConfigListEntry(_('Replace UK channel names in bouquets with swap names'), self.EpgSwapNamesCfg))    
				self.list.append(getConfigListEntry(_('UK only: Force UK name swap'), self.ForceRytecUKCfg))  
				
			if self.EpgProviderCfg.value == True and jglob.has_epg_importer:
				self.list.append(getConfigListEntry(_('EPG url'), self.XmltvCfg))

		else:
			self.list.append(getConfigListEntry(_('Live categories'), self.LiveCategoriesCfg))
			
			if self.LiveCategoriesCfg.value == True:
				self.list.append(getConfigListEntry(_('Stream type for Live'), self.LiveTypeCfg))

			self.list.append(getConfigListEntry(_('Vod categories'), self.VodCategoriesCfg))
			
			self.list.append(getConfigListEntry(_('Series categories'), self.SeriesCategoriesCfg))

			if self.VodCategoriesCfg.value == True or self.SeriesCategoriesCfg.value == True:
				self.list.append(getConfigListEntry(_('Stream type for VOD/Series'), self.VodTypeCfg))
			   
			
			if self.LiveCategoriesCfg.value == True and jglob.has_epg_importer:
				self.list.append(getConfigListEntry(_('Use your provider EPG'), self.EpgProviderCfg))
		
			if self.EpgProviderCfg.value == True and jglob.has_epg_importer:  
				self.list.append(getConfigListEntry(_('EPG url'), self.XmltvCfg))
				
		self['config'].list = self.list
		self['config'].l.setList(self.list)
		
		self.setInfo()
		 
		self.handleInputHelpers()
		
	# dreamos workaround for showing setting descriptions
	def setInfo(self):
		
		entry = str(self.getCurrentEntry())

		if entry == _('Bouquet name'):
			self['information'].setText(_("\nEnter name to be shown as a prefix in your bouquets"))
			return
			
		if entry == _('Use name as bouquet prefix'):
			self['information'].setText(_("\nUse provider name prefix in your bouquets"))
			return
			
		if entry == _('Live categories'):
			self['information'].setText(_("\nInclude LIVE categories in your bouquets."))
			return
			
		if entry == _('Stream type for Live'):
			self['information'].setText(_("\nThis setting allows you to choose which player E2 will use for your live streams.\nIf your live streams do not play try changing this setting."))
			return
			
		if entry == _('VOD categories'):
			self['information'].setText(_("\nInclude VOD categories in your bouquets."))
			return
			
		if entry == _('Series categories'):
			self['information'].setText(_("\nInclude SERIES categories in your bouquets. \n** Note: Selecting Series can be slow to populate the lists.**"))
			return
			
		if entry == _('Stream type for VOD/SERIES'):
			self['information'].setText(_("\nThis setting allows you to choose which player E2 will use for your VOD/Series streams.\nIf your VOD streams do not play try changing this setting."))
			return
			
		if entry == _('VOD bouquet order'):
			self['information'].setText(_("\nSelect the sort order for your VOD Bouquets."))
			return
			
		if entry == _('Use your provider EPG'):
			self['information'].setText(_("\nMake provider xmltv for use in EPG Importer.\nProvider source needs to be selected in EPG Importer plugin."))
			return
			
		if entry == _('EPG url'):
			self['information'].setText(_("Enter the EPG url for your playlist. If unknown leave as default."))
			return
			
		if entry == _('Use Rytec UK EPG'):
			self['information'].setText(_("\nTry to match the UK Rytec names in the background to populate UK EPG.\nNote this will override your provider's UK EPG."))
			return
			
		if entry == _('Replace UK channel names in bouquets with swap names'):
			self['information'].setText(_("\nThis will amend the UK channels names in channel bouquets to that of the computed swap names."))
			return
			
		if entry == _('UK only: Force UK name swap'):
			self['information'].setText(_("Use for UK providers that do not specify UK in the category title or channel title.\nMay cause non UK channels to have the wrong epg.\nTrying creating bouquets without this option turned off first."))


	def handleInputHelpers(self):
		if self['config'].getCurrent() is not None:
			if isinstance(self['config'].getCurrent()[1], ConfigText) or isinstance(self['config'].getCurrent()[1], ConfigPassword):
				if self.has_key('VKeyIcon'):
					if isinstance(self['config'].getCurrent()[1], ConfigNumber):
						self['VirtualKB'].setEnabled(False)
						self['VKeyIcon'].hide()
					else:
						self['VirtualKB'].setEnabled(True)
						self['VKeyIcon'].show()
				
				if not isinstance(self['config'].getCurrent()[1], ConfigNumber):
					
					 if isinstance(self['config'].getCurrent()[1].help_window, ConfigText) or isinstance(self['config'].getCurrent()[1].help_window, ConfigPassword):
						if self['config'].getCurrent()[1].help_window.instance is not None:
							helpwindowpos = self['HelpWindow'].getPosition()

							if helpwindowpos:
								helpwindowposx, helpwindowposy = helpwindowpos
								if helpwindowposx and helpwindowposy:
									from enigma import ePoint
									self['config'].getCurrent()[1].help_window.instance.move(ePoint(helpwindowposx,helpwindowposy))
				
			else:
				if self.has_key('VKeyIcon'):
					self['VirtualKB'].setEnabled(False)
					self['VKeyIcon'].hide()
		else:
			if self.has_key('VKeyIcon'):
				self['VirtualKB'].setEnabled(False)
				self['VKeyIcon'].hide()
				

	def changedEntry(self):
		self.item = self['config'].getCurrent()
		for x in self.onChangedEntry:
			x()
			
		try:
			if isinstance(self['config'].getCurrent()[1], ConfigEnableDisable) or isinstance(self['config'].getCurrent()[1], ConfigYesNo) or isinstance(self['config'].getCurrent()[1], ConfigSelection):
				self.createSetup()
		except:
			pass


	def getCurrentEntry(self):
		return self['config'].getCurrent() and self['config'].getCurrent()[0] or ''

	def getCurrentValue(self):
		return self['config'].getCurrent() and str(self['config'].getCurrent()[1].getText()) or ''


	def save(self):
		jglob.name = self.NameCfg.value
		if jglob.old_name != jglob.name:
			if jglob.name.strip() == '' or jglob.name.strip() == None:
				self.session.open(MessageBox, _('Bouquet name cannot be blank. Please enter a unique bouquet name. Minimum 2 characters.'), MessageBox.TYPE_ERROR, timeout=10)
				self.createSetup()
				return
		
				
		for x in self['config'].list:
			x[1].save()
				
		self['config'].instance.moveSelectionTo(1)
		
		jglob.finished = False
		jglob.name = self.NameCfg.value
		jglob.prefix_name = self.PrefixNameCfg.value
		jglob.live = self.LiveCategoriesCfg.value
		jglob.live_type = self.LiveTypeCfg.value
		jglob.vod = self.VodCategoriesCfg.value
		jglob.series = self.SeriesCategoriesCfg.value
		jglob.vod_type = self.VodTypeCfg.value
		jglob.vod_order = self.VodOrderCfg.value
		jglob.epg_provider = self.EpgProviderCfg.value
		jglob.epg_rytec_uk = self.EpgRytecUKCfg.value
		jglob.epg_swap_names = self.EpgSwapNamesCfg.value
		jglob.epg_force_rytec_uk = self.ForceRytecUKCfg.value
		
		jglob.xmltv_address = self.XmltvCfg.value
		
		self.session.openWithCallback(self.finishedCheck, JediMakerXtream_ChooseBouquets)

	def cancel(self):
		self.close()


	def finishedCheck(self):
		self.createSetup()
		if jglob.finished:
			self.close()
	

class JediMakerXtream_ChooseBouquets(Screen):

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		
		skin = skin_path + 'jmx_bouquets.xml'
		with open(skin, 'r') as f:
			self.skin = f.read()
			
		self.setup_title = _('Choose Bouquets')
		
		self.startList = []
		self.drawList = []
		
		self.pause = 100
		
		self['list'] = List(self.drawList) 
		
		self['key_red'] = StaticText('')
		self['key_green'] = StaticText('')
		self['key_yellow'] = StaticText('')
		self['key_blue'] = StaticText('')
		self['key_info'] = StaticText('')
		self['description'] = Label('')
		self['lab1'] = Label(_('Loading data... Please wait...'))
		
		self['setupActions'] = ActionMap(['ColorActions', 'SetupActions', 'ChannelSelectEPGActions'], {
			 'red': self.keyCancel,
			 'green': self.keyGreen,
			 'yellow': self.toggleAllSelection,
			 'blue': self.clearAllSelection,
			 'save': self.keyGreen,
			 'cancel': self.keyCancel,
			 'ok': self.toggleSelection,
			 'info': self.viewChannels,
			 'showEPGList': self.viewChannels
			 }, -2)
			 
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Create'))
		self['key_yellow'] = StaticText(_('Invert'))
		self['key_blue'] = StaticText(_('Clear All'))
		self['key_info'] = StaticText(_('Show Channels'))
		self['description'] = Label(_('Select the playlist categories you wish to create bouquets for.\nPress OK to invert the selection.\nPress INFO to show the channels in this category.'))
		
		self['list'].onSelectionChanged.append(self.getCurrentEntry)
		
		self.cat_list = ''
		self.currentSelection = 0
		
		self.playlisttype = jglob.current_playlist['playlist_info']['playlisttype']
		

		if self.playlisttype == 'xtream':
			protocol = jglob.current_playlist['playlist_info']['protocol']
			domain = jglob.current_playlist['playlist_info']['domain']
			port = str(jglob.current_playlist['playlist_info']['port'])   
			host = str(protocol) + str(domain) + ':' + str(port) + '/' 
			username = jglob.current_playlist['playlist_info']['username']
			password = jglob.current_playlist['playlist_info']['password']
			player_api = str(host) + 'player_api.php?username=' + str(username) + '&password=' + str(password)
			
			self.LiveCategoriesUrl = player_api + '&action=get_live_categories'
			self.VodCategoriesUrl = player_api + '&action=get_vod_categories'
			self.SeriesCategoriesUrl = player_api + '&action=get_series_categories'
		
			self.LiveStreamsUrl = player_api + '&action=get_live_streams'
			self.VodStreamsUrl = player_api + '&action=get_vod_streams'
			self.SeriesUrl = player_api + '&action=get_series'
			
			if jglob.live:
				self['lab1'].setText('Downloading Live data')
				
				self.timer = eTimer()
				self.timer.start(self.pause, 1)
				try: 
					self.timer_conn = self.timer.timeout.connect(self.downloadLive)
				except:
					self.timer.callback.append(self.downloadLive)
					
			elif jglob.vod:
				self['lab1'].setText('Downloading VOD data')
				
				self.timer = eTimer()
				self.timer.start(self.pause, 1)
				try: 
					self.timer_conn = self.timer.timeout.connect(self.downloadVod)
				except:
					self.timer.callback.append(self.downloadVod)
					
			elif jglob.series:
				self['lab1'].setText('Downloading Series data')
				
				self.timer = eTimer()
				self.timer.start(self.pause, 1)
				try:
					self.timer_conn = self.timer.timeout.connect(self.downloadSeries)
				except:
					self.timer.callback.append(self.downloadSeries)
					
			else:
				self.close()
 
		else:
			self.onFirstExecBegin.append(self.m3uStart)
		self.onLayoutFinish.append(self.__layoutFinished)
		

		
	def __layoutFinished(self):
		self.setTitle(self.setup_title)
		self.getCurrentEntry()
		
		
	def downloadLive(self):

		downloads.downloadlivestreams(self.LiveStreamsUrl)
		
		if jglob.vod:
			self['lab1'].setText('Downloading VOD data')
			
			self.timer = eTimer()
			self.timer.start(self.pause, 1)
			try:
				self.timer_conn = self.timer.timeout.connect(self.downloadVod)
			except:
				self.timer.callback.append(self.downloadVod)
		
		elif jglob.series:
			self['lab1'].setText('Downloading Series data')
			
			self.timer = eTimer()
			self.timer.start(self.pause, 1)
			try: 
				self.timer_conn = self.timer.timeout.connect(self.downloadSeries)
			except:
				self.timer.callback.append(self.downloadSeries)
		else:
			self['lab1'].setText('Removing empty categories')
			self.timer = eTimer()
			self.timer.start(self.pause, 1)
			try: 
				self.timer_conn = self.timer.timeout.connect(self.checkcategories)
			except:
				self.timer.callback.append(self.checkcategories)
				

	def downloadVod(self):
		downloads.downloadvodstreams(self.VodStreamsUrl)
	
		if jglob.series:
			self['lab1'].setText('Downloading Series data')
			
			self.timer = eTimer()
			self.timer.start(self.pause, 1)
			try:
				self.timer_conn = self.timer.timeout.connect(self.downloadSeries)
			except:
				self.timer.callback.append(self.downloadSeries)
		else:
			self['lab1'].setText('Removing empty categories')
			self.timer = eTimer()
			self.timer.start(self.pause, 1)
			try: 
				self.timer_conn = self.timer.timeout.connect(self.checkcategories)
			except:
				self.timer.callback.append(self.checkcategories)
				
				
	def downloadSeries(self):
		downloads.downloadseriesstreams(self.SeriesUrl)
	
		self['lab1'].setText('Removing empty categories')
		self.timer = eTimer()
		self.timer.start(self.pause, 1)
		try: 
			self.timer_conn = self.timer.timeout.connect(self.checkcategories)
		except:
			self.timer.callback.append(self.checkcategories)
		

		
	def checkcategories(self):
		
		jfunc.checkcategories(jglob.live ,jglob.vod, jglob.series)
		
		self['lab1'].setText('Getting selection list')
		self.timer = eTimer()
		self.timer.start(self.pause, 1)
		try: 
			self.timer_conn = self.timer.timeout.connect(self.ignorelist)
		except:
			self.timer.callback.append(self.ignorelist)
			
	def ignorelist(self):
		# Only select previously selected categories or new categories
		if 'bouquet_info' in jglob.current_playlist and jglob.current_playlist['bouquet_info'] != {}:
			jfunc.IgnoredCategories(jglob.live, jglob.vod, jglob.series)
			
		self.timer = eTimer()
		self.timer.start(self.pause, 1)
		try:
			self.timer_conn = self.timer.timeout.connect(self.getStartList)
		except:
			self.timer.callback.append(self.getStartList)
			

		
	def buildListEntry(self, name, streamtype, index, enabled):
		if enabled:
			pixmap = LoadPixmap(cached=True, path=skin_path + "images/lock_on.png")
		else:
			pixmap = LoadPixmap(cached=True, path=skin_path + "images/lock_off.png")

		return(pixmap, str(name), str(streamtype), index, enabled)
		
		
	def getStartList(self):
		self['lab1'].setText('')
		self.drawList = [self.buildListEntry(x[0],x[1],x[2],x[3]) for x in jglob.categories]
		self.refresh()          
		
		
	def refresh(self):
		self.drawList = []
		self.drawList = [self.buildListEntry(x[0],x[1],x[2], x[3]) for x in jglob.categories]
		self['list'].updateList(self.drawList)
		
		
	def toggleSelection(self):
		if len(self['list'].list) > 0:
			idx = self['list'].getIndex()
			jglob.categories[idx][3] = not jglob.categories[idx][3]
			self.refresh()  
			
			
	def toggleAllSelection(self):
		for idx, item in enumerate(self['list'].list):
			jglob.categories[idx][3] = not jglob.categories[idx][3]
		self.refresh()  
		
		
	def getSelectionsList(self):
		return [(item[0], item[1], item[2], item[3]) for item in jglob.categories if item[3]]
		
	def getUnSelectedList(self):
		return [(item[0], item[1], item[2], item[3]) for item in jglob.categories if item[3] == False]
		
		
	def clearAllSelection(self):
		for idx, item in enumerate(self['list'].list):
			jglob.categories[idx][3] = False
		self.refresh() 
	

	def getCurrentEntry(self):
		self.currentSelection = self['list'].getIndex()


	def viewChannels(self):
		import viewchannel
		try:
			self.session.open(viewchannel.JediMakerXtream_ViewChannels, jglob.categories[self.currentSelection])
		except:
			return
		


	def m3uStart(self):
		downloads.getM3uCategories(jglob.live, jglob.vod)
		self.makeBouquetData()
		self.session.open(buildbouquet.JediMakerXtream_BuildBouquets)
		self.close()


	def keyCancel(self):
		self.close()
		 

	def keyGreen(self):

		selectedCategories = self.getSelectionsList()
		for selected in selectedCategories:
			if selected[1] == 'Live':
				jglob.live = True
				continue
			if selected[1] == 'VOD':
				jglob.vod = True
				continue
			if selected[1] == 'Series':
				jglob.series = True
				continue
			if jglob.live and jglob.vod and jglob.series:
				break

		self.makeBouquetData()
		self.session.openWithCallback(self.close, buildbouquet.JediMakerXtream_BuildBouquets)
		
 
	def makeBouquetData(self):
		
		jglob.current_playlist['bouquet_info'] = {}
		jglob.current_playlist['bouquet_info'] = OrderedDict([ 
		('bouquet_id', jglob.bouquet_id),
		('name', jglob.name),
		('oldname', jglob.old_name),
		('live_type', jglob.live_type),
		('vod_type', jglob.vod_type),
		('selected_live_categories', []),
		('selected_vod_categories', []),
		('selected_series_categories', []),
		('ignored_live_categories', []),
		('ignored_vod_categories', []),
		('ignored_series_categories', []),
		('live_update', '---'),
		('vod_update',  '---'),
		('series_update',  '---'),
		('xmltv_address', jglob.xmltv_address),
		('vod_order', jglob.vod_order),
		('epg_provider', jglob.epg_provider),
		('epg_rytec_uk', jglob.epg_rytec_uk),
		('epg_swap_names', jglob.epg_swap_names),
		('epg_force_rytec_uk', jglob.epg_force_rytec_uk),
		('prefix_name', jglob.prefix_name),
		 ])

		if jglob.live:
			jglob.current_playlist['bouquet_info']['live_update'] = datetime.now().strftime('%x  %X')
				
		if jglob.vod:
			jglob.current_playlist['bouquet_info']['vod_update'] = datetime.now().strftime('%x  %X')
			
		if jglob.series:
			jglob.current_playlist['bouquet_info']['series_update'] = datetime.now().strftime('%x  %X')
	
	
		if self.playlisttype == 'xtream':
			jglob.selectedcategories = self.getSelectionsList()
			
			for category in jglob.selectedcategories:
				if category[1] == 'Live':
					jglob.current_playlist['bouquet_info']['selected_live_categories'].append(category[0])
				elif category[1] == 'Series':
					jglob.current_playlist['bouquet_info']['selected_series_categories'].append(category[0])
				elif category[1] == 'VOD':
					jglob.current_playlist['bouquet_info']['selected_vod_categories'].append(category[0])
					
			jglob.ignoredcategories = self.getUnSelectedList()
			
			for category in jglob.ignoredcategories:
				if category[1] == 'Live':
					jglob.current_playlist['bouquet_info']['ignored_live_categories'].append(category[0])
				elif category[1] == 'Series':
					jglob.current_playlist['bouquet_info']['ignored_series_categories'].append(category[0])
				elif category[1] == 'VOD':
					jglob.current_playlist['bouquet_info']['ignored_vod_categories'].append(category[0])
					
			
		else:
			for category in jglob.getm3ustreams:
				if category[4] == 'live' and category[0] not in jglob.current_playlist['bouquet_info']['selected_live_categories']:
					jglob.current_playlist['bouquet_info']['selected_live_categories'].append(category[0])
				elif category[4] == 'vod' and category[0] not in jglob.current_playlist['bouquet_info']['selected_vod_categories']:
					jglob.current_playlist['bouquet_info']['selected_vod_categories'].append(category[0])
		
		self.playlists_all = jfunc.getPlaylistJson()
		
		for playlist in self.playlists_all:
			if playlist['playlist_info']['index'] == jglob.current_playlist['playlist_info']['index']:
				playlist['bouquet_info'] = jglob.current_playlist['bouquet_info']

				break
			
		with open(playlist_file, 'w') as f:
			json.dump(self.playlists_all, f)
			
	   
