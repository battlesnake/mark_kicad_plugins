# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-88b0f50)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class BoredUserEntertainerDesign
###########################################################################

class BoredUserEntertainerDesign ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Mark's plugin", pos = wx.DefaultPosition, size = wx.Size( 400,100 ), style = wx.CAPTION|wx.FRAME_FLOAT_ON_PARENT|wx.FRAME_NO_TASKBAR|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		root_sizer = wx.BoxSizer( wx.VERTICAL )


		root_sizer.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.caption_label = wx.StaticText( self, wx.ID_ANY, u"Working, please wait...", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL )
		self.caption_label.Wrap( -1 )

		root_sizer.Add( self.caption_label, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.progress_gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.progress_gauge.SetValue( 0 )
		root_sizer.Add( self.progress_gauge, 0, wx.ALIGN_CENTER_HORIZONTAL, 20 )


		root_sizer.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		self.SetSizer( root_sizer )
		self.Layout()

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


