# coding=utf-8
"""Author: Michal Wrona
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Class responsible for loading generators.
"""

import imp
import os


class PluginsLoader:
    """Loads generators (all python files) from 'generators' directory.
    Each generator will be available under key created from its filename.
    """

    def __init__(self):
        self.plugins = {}
        file_location = os.path.dirname(os.path.realpath(__file__))
        generators_path = os.path.join(file_location, "..", "generators")
        plugins_files = [os.path.splitext(f)[0] for f in
                         os.listdir(generators_path) if f.endswith('.py')]
        for p in plugins_files:
            self.plugins[p] = imp.load_module(p, *imp.find_module(p, [
                generators_path]))

    def get_plugin(self, name):
        return self.plugins[name]

    def get_available_plugins(self):
        return self.plugins.keys()
