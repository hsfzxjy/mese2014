"""
	Copy from django.db -.-
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import SortedDict
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule
from django.utils._os import upath
from django.utils import six

import imp
import sys
import os

class AppCache(object):
	"""
	A cache that stores installed applications and their router. Used to
	provide reverse-relations and for app introspection (e.g. admin).
	"""
	__shared_state = dict(
		app_store=SortedDict(),
		app_labels={},
		app_routers=[],
		app_errors={},
		loaded=False,
		handled={},
		postponed=[],
		nesting_level=0,
		_get_router_cache={},
	)

	def __init__(self):
		self.__dict__ = self.__shared_state
		pass

	def _populate(self):
		"""
		Fill in all the cache information. This method is threadsafe, in the
		sense that every caller will see the same state upon return, and if the
		cache is already initialised, it does no work.
		"""
		if self.loaded:
			return
		imp.acquire_lock()
		try:
			if self.loaded:
				return
			for app_name in settings.INSTALLED_APPS:
				if app_name in self.handled:
					continue
				self.load_app(app_name, True)
			if not self.nesting_level:
				for app_name in self.postponed:
					print app_name
					self.load_app(app_name)
				self.loaded = True
		finally:
			imp.release_lock()

	def _label_for(self, app_mod):
		"""
		Return app_label for given router module.

		"""
		return app_mod.__name__.split('.')[-2]

	def get_routers(self):
		res = []
		for app in self.get_apps():
			res.extend(getattr(app, 'routes', []))
		return res
		
	def load_app(self, app_name, can_postpone=True):
		"""
		Loads the app with the provided fully qualified name, and returns the
		model module.
		"""
		self.handled[app_name] = None
		self.nesting_level += 1
		app_module = import_module(app_name)
		try:
			router = import_module('.routers', app_name)
		except ImportError:
			self.nesting_level -= 1
			if not module_has_submodule(app_module, 'routers'):
				return None
			else:
				if can_postpone:
					self.postponed.append(app_name)
					return None
				else:
					raise

		self.nesting_level -= 1
		if router not in self.app_store:
			self.app_store[router] = len(self.app_store)
			self.app_labels[self._label_for(router)] = router
		return router

	def get_apps(self):
		"Returns a list of all installed modules that contain router."
		self._populate()

		# Ensure the returned list is always in the same order (with new apps
		# added at the end). This avoids unstable ordering on the admin app
		# list page, for example.
		apps = [(v, k) for k, v in self.app_store.items()]
		apps.sort()
		return [elt[1] for elt in apps]

	def get_app(self, app_label, emptyOK=False):
		"""
		Returns the module containing the router for the given app_label. If
		the app has no router in it and 'emptyOK' is True, returns None.
		"""
		self._populate()
		imp.acquire_lock()
		try:
			for app_name in settings.INSTALLED_APPS:
				if app_label == app_name.split('.')[-1]:
					mod = self.load_app(app_name, False)
					if mod is None:
						if emptyOK:
							return None
						raise ImproperlyConfigured("App with label %s is missing a router.py module." % app_label)
					else:
						return mod
			raise ImproperlyConfigured("App with label %s could not be found" % app_label)
		finally:
			imp.release_lock()

	def get_app_errors(self):
		"Returns the map of known problems with the INSTALLED_APPS."
		self._populate()
		return self.app_errors

cache = AppCache()