# coding: utf-8
# Copyright (C) 2016 Bruno Abude Cardoso
#
# Imagem Cinemática is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Imagem Cinemática is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pickle

from ic import messages

settings = {}

def change(name, value):
    name = name.lower()
    settings[name] = value
    messages.post("SETTING_changed", ";".join([name, str(value)]))
    return value

def get(name):
    return settings.get(name.lower(), None)

def load(file_path):
    with open(file_path, "r") as f:
        unpickled = pickle.load(f)
        for key in unpickled:
            change(key, unpickled[key])

def save(file_path):
    with open(file_path, "w") as f:
        pickle.dump(settings, file_path)
