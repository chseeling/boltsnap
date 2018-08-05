import sys,os
import curses
from subprocess import check_output
import json
from geoip import geolite2        # https://pypi.org/project/python-geoip-python3/
from hurry.filesize import size
import time

def renderPeerStr(peer):
	if peer is None:
		return " "*20 + "\t" + "Bsent" + "\t" + "Brecv" + "\theight" + "\tconnTime" 
	addr = peer['addr'].split(':')[0]
	match = geolite2.lookup(addr)
	country = '  '
	if match:
		country = match.country
	sb = "     "
	if 'synced_blocks' in peer:
		sb = str(peer['synced_blocks'])
	conntime = time.strftime('%m-%d %H:%M:%S', time.localtime(peer['conntime']))
	return country + " " + addr.ljust(17) +"\t" + \
               size(peer['bytessent']) + "\t" + size(peer['bytesrecv']) + \
               "\t" + sb + "\t" + conntime + "\t" + peer['subver']

def renderLNPeerStr(peer):
	if peer is None:
		return " "*20 + "\tBsent\tBrecv"
	addr = peer['address'].split(':')[0]
	match = geolite2.lookup(addr)
	country = '  '
	if match:
		country = match.country
	return country + " " + addr.ljust(17) + peer["bytes_sent"].rjust(9) + \
               "\t" + peer["bytes_recv"].rjust(9)

def renderLNChannelStr(channel):
	return channel['local_balance'].rjust(8) + "\t" + channel['remote_balance'].rjust(8)


def draw_menu(stdscr):
	k = 0
	cursor_x = 0
	cursor_y = 0

	# Clear and refresh the screen for a blank canvas
	stdscr.clear()
	stdscr.refresh()

	# Start colors in curses
	curses.start_color()
	curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

	curses.halfdelay(20)
	# Loop where k is the last character pressed
	cnt = -1
	len_ln_graph = None
	while (k != ord('q')):
		cnt = (cnt + 1) % 20000
		s = check_output(['bitcoin-cli','getpeerinfo'])
		peers_list = json.loads(s.decode('utf-8'))

		s = check_output(['lncli','listpeers'])
		ln_peers_list = json.loads(s.decode('utf-8'))
		ln_peers_list = sorted(ln_peers_list["peers"],key=lambda k: k['address'])

		if cnt == 1:
			s = check_output(['lncli','describegraph'])
			ln_graph = json.loads(s.decode('utf-8'))
			ln_graph = ln_graph["nodes"]
			len_ln_graph = len(ln_graph)

		s = check_output(['lncli','listchannels'])
		ln_channels_list = json.loads(s.decode('utf-8'))
		ln_channels_list = ln_channels_list["channels"]

		s = check_output(['bitcoin-cli','getmempoolinfo'])
		mempool_info = json.loads(s.decode('utf-8'))

	        # Initialization
		stdscr.clear()
		height, width = stdscr.getmaxyx()

		if k == curses.KEY_DOWN:
			cursor_y = cursor_y + 1
		elif k == curses.KEY_UP:
			cursor_y = cursor_y - 1
		elif k == curses.KEY_RIGHT:
			cursor_x = cursor_x + 1
		elif k == curses.KEY_LEFT:
			cursor_x = cursor_x - 1

		cursor_x = max(0, cursor_x)
		cursor_x = min(width-1, cursor_x)

		cursor_y = max(0, cursor_y)
		cursor_y = min(height-1, cursor_y)

		# Declaration of strings
		title = "bitcoind peers list"[:width-1]
		subtitle = peers_list[-1]["addr"][:width-1]
		statusbarstr = "'q' to exit | BTC Peers: {} LN Peers: {} Mempool Tx: {} LN Nodes: {}" \
                       .format(len(peers_list), len(ln_peers_list), mempool_info["size"], len_ln_graph)
		if k == 0:
			keystr = "No key press detected..."[:width-1]

		# Centering calculations
		start_x_title = 1
		start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)
		start_x_keystr = int((width // 2) - (len(keystr) // 2) - len(keystr) % 2)
		start_y = 0

		# Rendering some text
		#whstr = "Width: {}, Height: {}".format(width, height)
		#stdscr.addstr(0, 0, whstr, curses.color_pair(1))

		# Render status bar
		stdscr.attron(curses.color_pair(3))
		stdscr.addstr(height-1, 0, statusbarstr)
		stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
		stdscr.attroff(curses.color_pair(3))

		# Turning on attributes for title
		stdscr.attron(curses.color_pair(2))
		stdscr.attron(curses.A_BOLD)

		# Rendering title
		stdscr.addstr(start_y, start_x_title, title)

		# Turning off attributes for title
		stdscr.attroff(curses.color_pair(2))
		stdscr.attroff(curses.A_BOLD)

		# Print rest of text
		i = 0; total_sent = 0; total_recv = 0
		i += 1
		stdscr.addstr(start_y + i, 1, renderPeerStr(None) )
		for peer in peers_list:
			i += 1
			stdscr.addstr(start_y + i, 1, renderPeerStr(peer) )

		start_y = height - len(ln_peers_list) - 3
		i = 1
		stdscr.addstr(start_y + i, 1, renderLNPeerStr(None) )
		for peer in ln_peers_list:
			i += 1
			stdscr.addstr(start_y + i, 1, renderLNPeerStr(peer) )

		start_y = height - len(ln_channels_list) - 2
		i = 0
		for channel in ln_channels_list:
			i += 1
			stdscr.addstr(start_y + i, int(width/2+1), renderLNChannelStr(channel) )


		stdscr.move(cursor_y, cursor_x)

		# Refresh the screen
		stdscr.refresh()

		# Wait for next input
		k = stdscr.getch()

def main():
	curses.wrapper(draw_menu)

if __name__ == "__main__":
	main()
