import os
import struct
import sys
from collections import OrderedDict

class ModFileCreator():
	
	def __init__(self, dPath, modid):
		self.map_names = []  # Stores map names from mod.info
		self.meta_data = OrderedDict([])  # Stores key value from modmeta.info
		self.create_mod_file(dPath, modid)

	def create_mod_file(self, dPath, modid):
		if not self.parse_base_info(dPath, modid) or not self.parse_meta_data(dPath, modid):
			return False

		with open(os.path.join(dPath, modid + ".mod"), "w+b") as f:

			modid = int(modid)
			f.write(struct.pack('ixxxx', modid))  # Needs 4 pad bits
			self.write_ue4_string("ModName", f)
			self.write_ue4_string("", f)

			map_count = len(self.map_names)
			f.write(struct.pack("i", map_count))

			for m in self.map_names:
				self.write_ue4_string(m, f)

			# Not sure of the reason for this
			num2 = 4280483635
			f.write(struct.pack('I', num2))
			num3 = 2
			f.write(struct.pack('i', num3))

			if "ModType" in self.meta_data:
				mod_type = b'1'
			else:
				mod_type = b'0'

			f.write(struct.pack('p', mod_type))
			meta_length = len(self.meta_data)
			f.write(struct.pack('i', meta_length))

			for k, v in self.meta_data.items():
				self.write_ue4_string(k, f)
				self.write_ue4_string(v, f)

		return True

	def read_ue4_string(self, file):
		count = struct.unpack('i', file.read(4))[0]
		flag = False
		if count < 0:
			flag = True
			count -= 1

		if flag or count <= 0:
			return ""

		return file.read(count)[:-1].decode()

	def write_ue4_string(self, string_to_write, file):
		string_length = len(string_to_write) + 1
		file.write(struct.pack('i', string_length))
		barray = bytearray(string_to_write, "utf-8")
		file.write(barray)
		file.write(struct.pack('p', b'0'))

	def parse_meta_data(self, dPath, modid):
		"""
		Parse the modmeta.info files and extract the key value pairs need to for the .mod file.
		How To Parse modmeta.info:
			1. Read 4 bytes to tell how many key value pairs are in the file
			2. Read next 4 bytes tell us how many bytes to read ahead to get the key
			3. Read ahead by the number of bytes retrieved from step 2
			4. Read next 4 bytes to tell how many bytes to read ahead to get value
			5. Read ahead by the number of bytes retrieved from step 4
			6. Start at step 2 again
		:return: Dict
		"""

		mod_meta = os.path.join(dPath, modid, "modmeta.info")

		if not os.path.isfile(mod_meta):
			return False

		with open(mod_meta, "rb") as f:

			total_pairs = struct.unpack('i', f.read(4))[0]

			for i in range(total_pairs):

				key, value = "", ""

				key_bytes = struct.unpack('i', f.read(4))[0]
				key_flag = False
				if key_bytes < 0:
					key_flag = True
					key_bytes -= 1

				if not key_flag and key_bytes > 0:

					raw = f.read(key_bytes)
					key = raw[:-1].decode()

				value_bytes = struct.unpack('i', f.read(4))[0]
				value_flag = False
				if value_bytes < 0:
					value_flag = True
					value_bytes -= 1

				if not value_flag and value_bytes > 0:
					raw = f.read(value_bytes)
					value = raw[:-1].decode()

				# TODO This is a potential issue if there is a key but no value
				if key and value:
					self.meta_data[key] = value

		return True


	def parse_base_info(self, dPath, modid):
		mod_info = os.path.join(dPath, modid, "mod.info")

		if not os.path.isfile(mod_info):
			return False

		with open(mod_info, "rb") as f:
			self.read_ue4_string(f)
			map_count = struct.unpack('i', f.read(4))[0]

			for i in range(map_count):
				cur_map = self.read_ue4_string(f)
				if cur_map:
					self.map_names.append(cur_map)

		return True

# Args:
#
# 1) Mods folder for the server instance
# 2) Mod ID to generate .mod file for
if __name__ == "__main__":
    ModFileCreator(sys.argv[1], sys.argv[2])
