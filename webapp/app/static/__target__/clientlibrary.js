// Transcrypt'ed from Python, 2024-11-27 17:43:36
import {AssertionError, AttributeError, BaseException, DeprecationWarning, Exception, IndexError, IterableError, KeyError, NotImplementedError, RuntimeWarning, StopIteration, UserWarning, ValueError, Warning, __JsIterator__, __PyIterator__, __Terminal__, __add__, __and__, __call__, __class__, __envir__, __eq__, __floordiv__, __ge__, __get__, __getcm__, __getitem__, __getslice__, __getsm__, __gt__, __i__, __iadd__, __iand__, __idiv__, __ijsmod__, __ilshift__, __imatmul__, __imod__, __imul__, __in__, __init__, __ior__, __ipow__, __irshift__, __isub__, __ixor__, __jsUsePyNext__, __jsmod__, __k__, __kwargtrans__, __le__, __lshift__, __lt__, __matmul__, __mergefields__, __mergekwargtrans__, __mod__, __mul__, __ne__, __neg__, __nest__, __or__, __pow__, __pragma__, __pyUseJsNext__, __rshift__, __setitem__, __setproperty__, __setslice__, __sort__, __specialattrib__, __sub__, __super__, __t__, __terminal__, __truediv__, __withblock__, __xor__, _sort, abs, all, any, assert, bin, bool, bytearray, bytes, callable, chr, delattr, dict, dir, divmod, enumerate, filter, float, getattr, hasattr, hex, input, int, isinstance, issubclass, len, list, map, max, min, object, oct, ord, pow, print, property, py_TypeError, py_iter, py_metatype, py_next, py_reversed, py_typeof, range, repr, round, set, setattr, sorted, str, sum, tuple, zip} from './org.transcrypt.__runtime__.js';
var __name__ = '__main__';
export var like_post = function (post_id) {
	var success_callback = function (response) {
		var like_button = document.querySelector ('#like-button-{}'.format (post_id));
		like_button.innerText = 'Likes: {}'.format (response ['like_count']);
	};
	window.fetch ('/like_post/{}'.format (post_id), dict ({'method': 'POST'})).then ((function __lambda__ (response) {
		return response.json ().then (success_callback);
	})).catch ((function __lambda__ (error) {
		return window.console.log ('Error liking post:', error);
	}));
};
export var init_dashboard_chart = function (labels, data) {
	var ctx = document.getElementById ('productionChart').getContext ('2d');
	window.Chart.py_new (ctx, dict ({'type': 'line', 'data': dict ({'labels': labels, 'datasets': [dict ({'label': 'Crop Production (tonnes)', 'data': data, 'borderColor': 'rgba(75, 192, 192, 1)', 'backgroundColor': 'rgba(75, 192, 192, 0.2)', 'fill': true, 'tension': 0.4})]}), 'options': dict ({'scales': dict ({'x': dict ({'title': dict ({'display': true, 'text': 'Year'})}), 'y': dict ({'title': dict ({'display': true, 'text': 'Production (tonnes)'})})})})}));
};

//# sourceMappingURL=clientlibrary.map