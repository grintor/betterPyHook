# Microsoft API documentation: https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-setwindowshookexw
from ctypes import wintypes, windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref, Structure, cast, c_uint, sizeof
import atexit
import threading
import winreg
import time

with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Control Panel\Desktop', 0, winreg.KEY_WRITE) as key:
	winreg.SetValueEx(key, 'LowLevelHooksTimeout', 0, winreg.REG_DWORD, 10000)

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

class POINT(Structure):
	_fields_ = [ ("x", wintypes.LONG), ("y", wintypes.LONG)]

class MSLLHOOKSTRUCT(Structure):
	_fields_ = [
		("pt", POINT),
		("mouseData", wintypes.DWORD),
		("flags", wintypes.DWORD),
		("time", wintypes.DWORD),
		("dwExtraInfo", wintypes.ULONG)
		]
PMSLLHOOKSTRUCT = POINTER(MSLLHOOKSTRUCT)

class LASTINPUTINFO(Structure):
	_fields_ = [
		('cbSize', c_uint),
		('dwTime', c_uint),
	]
lastInputInfo = LASTINPUTINFO()

def GetLastInputInfo():
	lastInputInfo.cbSize = sizeof(lastInputInfo)
	windll.user32.GetLastInputInfo(byref(lastInputInfo))
	return lastInputInfo.dwTime

def listener(keyboard_callback, mouse_callback):
	def watchDogThread():
		global lastEventTime_global
		#print('watchdog in progress...')
		while True:
			time.sleep(1)
			if GetLastInputInfo() - 15000 > lastEventTime_global: # 15 secs ago
				#print('hook event is 15 secs behind.')
				rehook()
				lastEventTime_global = GetLastInputInfo()
					
	def chaosMonkey():
		print('chaos started')
		while True:
			time.sleep(10)
			print('chaos strikes!')
			unhook()
		
	def rehook():
		unhook()
		threading.Thread(target=startHook).start()
		
	def unhook():
		windll.user32.UnhookWindowsHookEx(keyboard_hook_id)
		windll.user32.UnhookWindowsHookEx(mouse_hook_id)
		
	def startHook():
		global keyboard_hook_id
		global mouse_hook_id
	
		# Our low level handler signature.
		CMPFUNC = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
		# Convert the Python keyboard handler into C pointer.
		keyboard_ll_pointer = CMPFUNC(keyboard_low_level_handler)
		# Convert the Python mouse handler into C pointer.
		mouse_ll_pointer = CMPFUNC(mouse_low_level_handler)
		#Added 4-18-15 for move to ctypes:
		windll.kernel32.GetModuleHandleW.restype = wintypes.HMODULE
		windll.kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
		# argtypes required for x64 because default values overflow
		windll.user32.SetWindowsHookExW.argtypes = (c_int, wintypes.HANDLE, wintypes.HMODULE, wintypes.DWORD)

		# Hook keyboard
		keyboard_hook_id = windll.user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_ll_pointer, windll.kernel32.GetModuleHandleW(None), 0)
		# Hook mouse
		mouse_hook_id = windll.user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_ll_pointer, windll.kernel32.GetModuleHandleW(None), 0)

		orig_keyboard_hook_id = keyboard_hook_id
		while True:
			msg = windll.user32.GetMessageW(None, 0, 0,0)
			windll.user32.TranslateMessage(byref(msg))
			windll.user32.DispatchMessageW(byref(msg))

	def keyboard_low_level_handler(nCode, wParam, lParam):
		global lastEventTime_global
		lastEventTime_global = lParam[3]
		
		# we don't have time to wait around for some function exit, we have a hook to return
		threading.Thread(target=keyboard_callback, args=(
															wParam,		# wParam
															lParam[0],	# vkCode
															lParam[1],	# scanCode
															lParam[2],	# flags
															lParam[3],	# time
														)).start()
		#Be quick, return next hook
		return windll.user32.CallNextHookEx(keyboard_hook_id, nCode, wParam, lParam)

	def mouse_low_level_handler(nCode, wParam, lParam):
		_lParam = cast(lParam, PMSLLHOOKSTRUCT)[0]
		global lastEventTime_global
		lastEventTime_global = _lParam.time
		
		# we don't have time to wait around for some function exit, we have a hook to return
		if wParam != 512: # 512 is mouse movement
			threading.Thread(target=mouse_callback, args=(
																 wParam, 					   # wParam
																(_lParam.pt.x, _lParam.pt.y),  # pt
																 _lParam.mouseData,            # mouseData
																 _lParam.flags,                # flags
																 _lParam.time,                 # time
														  )).start()
		#Be quick, return next hook
		return windll.user32.CallNextHookEx(mouse_hook_id, nCode, wParam, lParam)


	threading.Thread(target=watchDogThread).start()
	#threading.Thread(target=chaosMonkey).start()
	threading.Thread(target=startHook).start()
	
	# Register to remove the hooks when the interpreter exits.
	atexit.register(unhook)
	



#virtual keycode constant names to virtual keycodes numerical id
vk_to_id = {'VK_LBUTTON' : 0x01, 'VK_RBUTTON' : 0x02, 'VK_CANCEL' : 0x03, 'VK_MBUTTON' : 0x04,
	'VK_BACK' : 0x08, 'VK_TAB' : 0x09, 'VK_CLEAR' : 0x0C, 'VK_RETURN' : 0x0D, 'VK_SHIFT' : 0x10,
	'VK_CONTROL' : 0x11, 'VK_MENU' : 0x12, 'VK_PAUSE' : 0x13, 'VK_CAPITAL' : 0x14, 'VK_KANA' : 0x15,
	'VK_HANGEUL' : 0x15, 'VK_HANGUL' : 0x15, 'VK_JUNJA' : 0x17, 'VK_FINAL' : 0x18, 'VK_HANJA' : 0x19,
	'VK_KANJI' : 0x19, 'VK_ESCAPE' : 0x1B, 'VK_CONVERT' : 0x1C, 'VK_NONCONVERT' : 0x1D, 'VK_ACCEPT' : 0x1E,
	'VK_MODECHANGE' : 0x1F, 'VK_SPACE' : 0x20, 'VK_PRIOR' : 0x21, 'VK_NEXT' : 0x22, 'VK_END' : 0x23,
	'VK_HOME' : 0x24, 'VK_LEFT' : 0x25, 'VK_UP' : 0x26, 'VK_RIGHT' : 0x27, 'VK_DOWN' : 0x28,
	'VK_SELECT' : 0x29, 'VK_PRINT' : 0x2A, 'VK_EXECUTE' : 0x2B, 'VK_SNAPSHOT' : 0x2C, 'VK_INSERT' : 0x2D,
	'VK_DELETE' : 0x2E, 'VK_HELP' : 0x2F, 'VK_LWIN' : 0x5B, 'VK_RWIN' : 0x5C, 'VK_APPS' : 0x5D,
	'VK_NUMPAD0' : 0x60, 'VK_NUMPAD1' : 0x61, 'VK_NUMPAD2' : 0x62, 'VK_NUMPAD3' : 0x63, 'VK_NUMPAD4' : 0x64,
	'VK_NUMPAD5' : 0x65, 'VK_NUMPAD6' : 0x66, 'VK_NUMPAD7' : 0x67, 'VK_NUMPAD8' : 0x68, 'VK_NUMPAD9' : 0x69,
	'VK_MULTIPLY' : 0x6A, 'VK_ADD' : 0x6B, 'VK_SEPARATOR' : 0x6C, 'VK_SUBTRACT' : 0x6D, 'VK_DECIMAL' : 0x6E,
	'VK_DIVIDE' : 0x6F ,'VK_F1' : 0x70, 'VK_F2' : 0x71, 'VK_F3' : 0x72, 'VK_F4' : 0x73, 'VK_F5' : 0x74,
	'VK_F6' : 0x75, 'VK_F7' : 0x76, 'VK_F8' : 0x77, 'VK_F9' : 0x78, 'VK_F10' : 0x79, 'VK_F11' : 0x7A,
	'VK_F12' : 0x7B, 'VK_F13' : 0x7C, 'VK_F14' : 0x7D, 'VK_F15' : 0x7E, 'VK_F16' : 0x7F, 'VK_F17' : 0x80,
	'VK_F18' : 0x81, 'VK_F19' : 0x82, 'VK_F20' : 0x83, 'VK_F21' : 0x84, 'VK_F22' : 0x85, 'VK_F23' : 0x86,
	'VK_F24' : 0x87, 'VK_NUMLOCK' : 0x90, 'VK_SCROLL' : 0x91, 'VK_LSHIFT' : 0xA0, 'VK_RSHIFT' : 0xA1,
	'VK_LCONTROL' : 0xA2, 'VK_RCONTROL' : 0xA3, 'VK_LMENU' : 0xA4, 'VK_RMENU' : 0xA5, 'VK_PROCESSKEY' : 0xE5,
	'VK_ATTN' : 0xF6, 'VK_CRSEL' : 0xF7, 'VK_EXSEL' : 0xF8, 'VK_EREOF' : 0xF9, 'VK_PLAY' : 0xFA,
	'VK_ZOOM' : 0xFB, 'VK_NONAME' : 0xFC, 'VK_PA1' : 0xFD, 'VK_OEM_CLEAR' : 0xFE, 'VK_BROWSER_BACK' : 0xA6,
	'VK_BROWSER_FORWARD' : 0xA7, 'VK_BROWSER_REFRESH' : 0xA8, 'VK_BROWSER_STOP' : 0xA9, 'VK_BROWSER_SEARCH' : 0xAA,
	'VK_BROWSER_FAVORITES' : 0xAB, 'VK_BROWSER_HOME' : 0xAC, 'VK_VOLUME_MUTE' : 0xAD, 'VK_VOLUME_DOWN' : 0xAE,
	'VK_VOLUME_UP' : 0xAF, 'VK_MEDIA_NEXT_TRACK' : 0xB0, 'VK_MEDIA_PREV_TRACK' : 0xB1, 'VK_MEDIA_STOP' : 0xB2,
	'VK_MEDIA_PLAY_PAUSE' : 0xB3, 'VK_LAUNCH_MAIL' : 0xB4, 'VK_LAUNCH_MEDIA_SELECT' : 0xB5, 'VK_LAUNCH_APP1' : 0xB6,
	'VK_LAUNCH_APP2' : 0xB7, 'VK_OEM_1' : 0xBA, 'VK_OEM_PLUS' : 0xBB, 'VK_OEM_COMMA' : 0xBC, 'VK_OEM_MINUS' : 0xBD,
	'VK_OEM_PERIOD' : 0xBE, 'VK_OEM_2' : 0xBF, 'VK_OEM_3' : 0xC0, 'VK_OEM_4' : 0xDB, 'VK_OEM_5' : 0xDC,
	'VK_OEM_6' : 0xDD, 'VK_OEM_7' : 0xDE, 'VK_OEM_8' : 0xDF, 'VK_OEM_102' : 0xE2, 'VK_PROCESSKEY' : 0xE5,
	'VK_PACKET' : 0xE7, 'VK_NOMAP' : 0xFF}

#inverse mapping of keycodes
id_to_vk = dict([(v,k) for k,v in vk_to_id.items()])