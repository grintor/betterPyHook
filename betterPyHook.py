# Microsoft API documentation: https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-setwindowshookexa
import ctypes
from ctypes import wintypes, windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref, Structure
from collections import namedtuple
from var_dump import var_dump
from time import sleep
import atexit
import threading

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

class POINT(Structure):
    _fields_ = [ ("x", ctypes.wintypes.LONG), ("y", ctypes.wintypes.LONG)] 

class MSLLHOOKSTRUCT(Structure):
    _fields_ = [ 
        ("pt", POINT),
        ("mouseData", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.wintypes.ULONG)
        ]
PMSLLHOOKSTRUCT = ctypes.POINTER(MSLLHOOKSTRUCT)

def listener():
	def keyboard_low_level_handler(nCode, wParam, lParam):
		# we don't have time to wait around for some function exit, we have a hook to return
		threading.Thread(target=print_keyboard_event, args=(wParam, lParam[0], lParam[1], lParam[2], lParam[3],)).start()
		#Be quick, return next hook
		return windll.user32.CallNextHookEx(keyboard_hook_id, nCode, wParam, lParam)
		
	def mouse_low_level_handler(nCode, wParam, lParam):
		lParam_decoded = ctypes.cast(lParam, PMSLLHOOKSTRUCT)
		mouseData = lParam_decoded[0].mouseData
		pt = (lParam_decoded[0].pt.x, lParam_decoded[0].pt.y)
		flags = lParam_decoded[0].flags
		time = lParam_decoded[0].time
		# we don't have time to wait around for some function exit, we have a hook to return
		threading.Thread(target=print_mouse_event, args=(wParam, pt, mouseData, flags, time,)).start()
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
	# Register to remove the hook when the interpreter exits.
	atexit.register(windll.user32.UnhookWindowsHookEx, keyboard_hook_id)
	atexit.register(windll.user32.UnhookWindowsHookEx, mouse_hook_id)
	
	while True:
		msg = windll.user32.GetMessageW(None, 0, 0,0)
		windll.user32.TranslateMessage(byref(msg))
		windll.user32.DispatchMessageW(byref(msg))


	def print_keyboard_event(wParam, vkCode, scanCode, flags, time):
		# flags  == 32  : alt_pressed
		# wParam == 256 : WM_KeyDown (normal key down)
		# wParam == 257 : WM_KeyUp (normal key up)
		# wParam == 260 : WM_SYSKEYDOWN (Alt Key Down)
		# wParam == 261 : WM_SYSKEYUP (Alt Key Up)
		
		print ('wParam: ' + str(wParam))
		print ('vkCode: ' + str(vkCode))
		print ('scanCode: ' + str(scanCode))
		print ('flags: ' + str(flags))
		print ('time: ' + str(time))
		
	def print_mouse_event(wParam, pt, mouseData, flags, time):
		# wParam == 512 : WM_MOUSEMOVE
		# wParam == 513 : WM_LBUTTONDOWN
		# wParam == 514 : WM_LBUTTONUP
		# wParam == 522 : WM_MOUSEWHEEL
		# wParam == 526 : WM_MOUSEHWHEEL
		# wParam == 516 : WM_RBUTTONDOWN 
		# wParam == 517 : WM_RBUTTONUP
		# mouseData : The high-order word of this member is WHEEL_DELTA. The low-order word is reserved.
		
		# WHEEL_DELTA:	A positive value indicates that the wheel was rotated forward, away from the user.
		#				A negative value indicates that the wheel was rotated backward, toward the user.
		WHEEL_DELTA = int.from_bytes(mouseData.to_bytes(4, byteorder='big')[:2], byteorder='big', signed=True)
		
		print ('wParam: ' + str(wParam))
		print ('pt: ' + str(pt))
		print ('WHEEL_DELTA: ' + str(WHEEL_DELTA))
		print ('flags: ' + str(flags))
		print ('time: ' + str(time))
		
if __name__ == '__main__':
	listener()
