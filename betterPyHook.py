# Microsoft API documentation: https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-setwindowshookexa
from ctypes import wintypes, windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref, Structure, POINTER, cast
import atexit
import threading

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

def listener(keyboard_callback, mouse_callback):
	def keyboard_low_level_handler(nCode, wParam, lParam):
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
		# we don't have time to wait around for some function exit, we have a hook to return
		threading.Thread(target=mouse_callback, args=(
															 wParam, 					   # wParam
															(_lParam.pt.x, _lParam.pt.y),  # pt
															 _lParam.mouseData,            # mouseData
															 _lParam.flags,                # flags
															 _lParam.time,                 # time
													  )).start()
		#Be quick, return next hook
		return windll.user32.CallNextHookEx(mouse_hook_id, nCode, wParam, lParam)

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
	windll.user32.SetWindowsHookExA.argtypes = (c_int, wintypes.HANDLE, wintypes.HMODULE, wintypes.DWORD)
	# Hook keyboard
	keyboard_hook_id = windll.user32.SetWindowsHookExA(WH_KEYBOARD_LL, keyboard_ll_pointer, windll.kernel32.GetModuleHandleW(None), 0)
	# Hook mouse
	mouse_hook_id = windll.user32.SetWindowsHookExA(WH_MOUSE_LL, mouse_ll_pointer, windll.kernel32.GetModuleHandleW(None), 0)
	# Register to remove the hooks when the interpreter exits.
	atexit.register(windll.user32.UnhookWindowsHookEx, keyboard_hook_id)
	atexit.register(windll.user32.UnhookWindowsHookEx, mouse_hook_id)

	while True:
		msg = windll.user32.GetMessageW(None, 0, 0,0)
		windll.user32.TranslateMessage(byref(msg))
		windll.user32.DispatchMessageW(byref(msg))
