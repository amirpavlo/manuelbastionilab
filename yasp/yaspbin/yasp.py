# This file was automatically generated by SWIG (http://www.swig.org).
# Version 3.0.12
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info >= (2, 7, 0):
    def swig_import_helper():
        import importlib
        pkg = __name__.rpartition('.')[0]
        mname = '.'.join((pkg, '_yasp')).lstrip('.')
        try:
            return importlib.import_module(mname)
        except ImportError:
            return importlib.import_module('_yasp')
    _yasp = swig_import_helper()
    del swig_import_helper
elif _swig_python_version_info >= (2, 6, 0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_yasp', [dirname(__file__)])
        except ImportError:
            import _yasp
            return _yasp
        try:
            _mod = imp.load_module('_yasp', fp, pathname, description)
        finally:
            if fp is not None:
                fp.close()
        return _mod
    _yasp = swig_import_helper()
    del swig_import_helper
else:
    import _yasp
del _swig_python_version_info

try:
    _swig_property = property
except NameError:
    pass  # Python < 2.2 doesn't have 'property'.

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_setattr_nondynamic(self, class_type, name, value, static=1):
    if (name == "thisown"):
        return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name, None)
    if method:
        return method(self, value)
    if (not static):
        if _newclass:
            object.__setattr__(self, name, value)
        else:
            self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)


def _swig_setattr(self, class_type, name, value):
    return _swig_setattr_nondynamic(self, class_type, name, value, 0)


def _swig_getattr(self, class_type, name):
    if (name == "thisown"):
        return self.this.own()
    method = class_type.__swig_getmethods__.get(name, None)
    if method:
        return method(self)
    raise AttributeError("'%s' object has no attribute '%s'" % (class_type.__name__, name))


def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except __builtin__.Exception:
    class _object:
        pass
    _newclass = 0

class yasp_logs(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, yasp_logs, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, yasp_logs, name)
    __repr__ = _swig_repr
    __swig_setmethods__["lg_error"] = _yasp.yasp_logs_lg_error_set
    __swig_getmethods__["lg_error"] = _yasp.yasp_logs_lg_error_get
    if _newclass:
        lg_error = _swig_property(_yasp.yasp_logs_lg_error_get, _yasp.yasp_logs_lg_error_set)
    __swig_setmethods__["lg_info"] = _yasp.yasp_logs_lg_info_set
    __swig_getmethods__["lg_info"] = _yasp.yasp_logs_lg_info_get
    if _newclass:
        lg_info = _swig_property(_yasp.yasp_logs_lg_info_get, _yasp.yasp_logs_lg_info_set)

    def __init__(self):
        this = _yasp.new_yasp_logs()
        try:
            self.this.append(this)
        except __builtin__.Exception:
            self.this = this
    __swig_destroy__ = _yasp.delete_yasp_logs
    __del__ = lambda self: None
yasp_logs_swigregister = _yasp.yasp_logs_swigregister
yasp_logs_swigregister(yasp_logs)

ERR_DEBUG = _yasp.ERR_DEBUG
ERR_INFO = _yasp.ERR_INFO
ERR_INFOCONT = _yasp.ERR_INFOCONT
ERR_WARN = _yasp.ERR_WARN
ERR_ERROR = _yasp.ERR_ERROR
ERR_FATAL = _yasp.ERR_FATAL
ERR_MAX = _yasp.ERR_MAX

def yasp_interpret(audioFile, transcript, output, genpath):
    return _yasp.yasp_interpret(audioFile, transcript, output, genpath)
yasp_interpret = _yasp.yasp_interpret

def yasp_interpret_get_str(audioFile, transcript, genpath):
    return _yasp.yasp_interpret_get_str(audioFile, transcript, genpath)
yasp_interpret_get_str = _yasp.yasp_interpret_get_str

def yasp_setup_logging(logs, cb, logfile):
    return _yasp.yasp_setup_logging(logs, cb, logfile)
yasp_setup_logging = _yasp.yasp_setup_logging

def yasp_finish_logging(logs):
    return _yasp.yasp_finish_logging(logs)
yasp_finish_logging = _yasp.yasp_finish_logging

def yasp_set_modeldir(modeldir):
    return _yasp.yasp_set_modeldir(modeldir)
yasp_set_modeldir = _yasp.yasp_set_modeldir

def yasp_free_json_str(json):
    return _yasp.yasp_free_json_str(json)
yasp_free_json_str = _yasp.yasp_free_json_str
# This file is compatible with both classic and new-style classes.


