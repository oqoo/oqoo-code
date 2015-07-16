/**
 * Created by Administrator on 2015/6/4.
 */
(function ($) {

    $.widget('mobile.xprogressbar', {
        initSelector: ":jqmData(role='xprogressbar')",
        version: 'BJC xprogressbar plugin 1.0.0',
        options: {
            outLog: true, // 是否显示log,
            //frontLabel: '前置标签',//03-05
            frontLabel: '03-05',//03-05
            //lastLabel: '后置标签',//<span>8</span>/12
            lastLabel: '<span>81</span>/12',//<span>8</span>/12
            barColor: '#ea3838',
            progress: '50'//0-100
        },

        _plugin: function () {
            $.extend(jQuery.easing, {
                backBoth: function (x, t, b, c, d, s) {
                    if (typeof s == 'undefined') {
                        s = 1.70158;
                    }
                    if ((t /= d / 2 ) < 1) {
                        return c / 2 * (t * t * (((s *= (1.525)) + 1) * t - s)) + b;
                    }
                    return c / 2 * ((t -= 2) * t * (((s *= (1.525)) + 1) * t + s) + 2) + b;
                }
            });
        },
        _create: function (option) {
            this._log('_create');
            this._plugin();
            //var labelF = $('<label class="date"></label>');
            //var labelL = $('<label class="progresstext"></label>');
            //var progressBar = $('<div class="bar1"><div class="bar2"></div></div>');
			
			//var table = $('<table width="100%" border="0" cellspacing="1" cellpadding="1"><tr><td width="1%" class="date"></td><td style="padding:1em"><div style="width:100%"><div class="bar1"><div class="bar2"></div></div></div></td><td width="1%" class="progresstext"><label ></label></td></tr></table>');
			
			var table = $('<div class="label clear"><span class="date"></span><span class="progresstext"></span></div>'
			+'<div class="bar1"><div class="bar2"></div></div>');

            this.element.addClass('ui-progressbar');
            this.element.append(table);
            //this.element.append(progressBar);
            //this.element.append(labelL);

            /*            var pl = parseInt(this._getStyle(this.element[0], 'paddingLeft'));
             var pr = parseInt(this._getStyle(this.element[0], 'paddingRight'));
             alert(this.element.width());
             progressBar.css('width', (this.element[0].offsetWidth - pl - pr) + 'px');*/
        },
        _init: function (option) {
            this._log('_init');
            if (option) this._setOptions(option);
            if (this.option('frontLabel')) {
                this.element.find('.date').html(this.option('frontLabel'));
            }
            if (this.option('lastLabel')) {
                this.element.find('.progresstext').html(this.option('lastLabel'));
            }
            if (this.option('barColor')) {
                this.element.find('.bar2').css('background-color', this.option('barColor'));
            }
            if (this.option('progress')) {
                this.element.find('.bar2').animate({
                    'width': this.option('progress') > 100 ? 100 : this.option('progress') + '%'
                }, 2000, 'backBoth');
                //this.element.find('.bar2').css('width', this.option('progress') + '%');
            }
        },
        _setOption: function (key, value) {
            console.log('_setOption: key=%s  value=%s', key, value);
            $.Widget.prototype._setOption.apply(this, arguments);
        },
        _setOptions: function (options) {
            for (key in options) {
                this._setOption(key, options[key]);
            }
            return this;
        },
        // 计算样式
        _getStyle: function (obj, attr) { // 建议使用此函数代替offsetWidth/height
            if (obj.currentStyle) {
                return obj.currentStyle[attr]; // ie
            } else {
                return getComputedStyle(obj, false)[attr];
            }
        },
        _log: function (str) {
            if (this.option('outLog'))
                console.log(this.version + ' [' + str + ']');
        }
    });
})(jQuery);