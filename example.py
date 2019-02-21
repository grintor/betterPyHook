import betterPyHook

def print_keyboard_event(wParam, vkCode, scanCode, flags, time):
	# flags	 == 32	: alt_pressed
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

print ('here we go...')

# this is forever-blocking, so maybe you should use threads or something
betterPyHook.listener(print_keyboard_event, print_mouse_event)
