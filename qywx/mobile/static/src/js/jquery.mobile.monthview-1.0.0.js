/**
 * Created by Administrator on 2015/6/4.
 */
(function ($) {

    $.widget('mobile.monthview', {
        initSelector: ":jqmData(role='monthview')",
        version: 'BJC monthview plugin 1.0.0',
        options: {
            outLog: false, // 是否显示log,
            startMonth: '',
            endMonth: '',
            currYear: new Date().getFullYear() // 2015
            /*monthData: [
             {month: 1, data: '' },
             {month: 2, data: {days: 18, hours: 188} },
             {month: 3, data: {days: 27, hours: 273} },
             {month: 4, data: {days: 1, hours: 11} },
             {month: 5, data: {days: 2, hours: 12} },
             {month: 6, data: {days: 3, hours: 13} },
             {month: 9, data: {days: 4, hours: 14} }
             ]*/

        },

        _create: function () {
            this._log('_create');
            this.element.addClass('ui-monthview');
            var table = document.createElement('table');
            // 标题caption ===========================================
            var caption = document.createElement('caption');
            var cLeftLeftBtn = document.createElement('div');
            var cLeftRightBtn = document.createElement('div');
            caption.innerHTML = "<&nbsp;<span></span>年&nbsp;>";
            caption.appendChild(cLeftLeftBtn);
            caption.appendChild(cLeftRightBtn);
            table.appendChild(caption);

            // 内容td =========================================
            for (var i = 1; i <= 4; i++) {
                var tr = $('<tr>');
                for (var ii = 1; ii <= 3; ii++) {
                    var td = $('<td><div><h3><span></span>月</h3><div class="content"></div></div></td>');
                    //<span class="days"></span>天&nbsp;<span class="hours"></span>小时
                    tr.append(td);
                }
                $(table).append(tr);
            }
            this.element.append(table);
        },

        _clearContent: function () {
            this.element.find('div.content').text('');
        },

        _formatTwo: function (num) {
            if (num < 10) return '0' + num;
            return num;
        },

        _init: function (option) {
            this._log('_init');
            this._setOptions(option);
            var _this = this;
            var startMonth = _this.options.startMonth && new Date(_this.options.startMonth).getTime();
            var endMonth = _this.options.endMonth && new Date(_this.options.endMonth).getTime();
            var currYear = _this.options.currYear;
            this.element.find('caption > div:first-of-type').unbind().on("touchend", function () {
                _this._init({'currYear': _this.option('currYear') - 1});
                _this._clearContent();
                _this.element.trigger('changeYear', _this.option('currYear') - 1);
            });
            this.element.find('caption > div:last-of-type').unbind().on("touchend", function () {
                _this._init({'currYear': _this.option('currYear') + 1});
                _this._clearContent();
                _this.element.trigger('changeYear', _this.option('currYear') + 1);
            });
            this.element.find('caption span').text(this.option('currYear'));
            var aTd = this.element.find('td');

            for (var i = 0, l = aTd.length; i < l; i++) {

                $(aTd[i]).find('div').removeClass('disable');

                $(aTd[i]).attr('disable', false);

                $(aTd[i]).find('h3 span').text(i + 1);

                // 判断是不是在开始结束范围内
                //$(aTd[i]).find('div').addClass('disable');
                var currMonth = new Date(currYear + '-' + _this._formatTwo(i + 1)).getTime();
                if (startMonth && endMonth) {
                    _this._log((i + 1) + "  " + startMonth + "  " + currMonth);
                    if (!(startMonth <= currMonth && endMonth >= currMonth)) {
                        $(aTd[i]).find('div').addClass('disable');
                        $(aTd[i]).attr('disable', true);
                    }
                } else if (startMonth) {
                    if (startMonth > currMonth) {
                        $(aTd[i]).find('div').addClass('disable');
                        $(aTd[i]).attr('disable', true);
                    }
                } else if (endMonth) {
                    if (endMonth < currMonth) {
                        $(aTd[i]).find('div').addClass('disable');
                        $(aTd[i]).attr('disable', true);
                    }
                }

                $(aTd[i]).attr({month: i + 1});
                $(aTd[i]).unbind().on('touchend', function () {
                    //_this.element.trigger('touchMonth', {month: $(this).attr('month'), days: $(this).attr('days'), hours: $(this).attr('hours')});
                    var m = $(this).attr('month') < 10 ? '0' + $(this).attr('month') : $(this).attr('month');
                    if (!eval($(this).attr('disable'))) {
                        _this.element.trigger('touchMonth', {month: _this.option('currYear') + '-' + m});
                    }
                });

                /*var md = this.option('monthData');
                 for (var attr in md) {
                 if (md[attr].month == i + 1) {
                 //$(aTd[i]).find('div').removeClass('disable');
                 //$(aTd[i]).find('div > div > span.days').text(md[attr].data.days);
                 //$(aTd[i]).attr('days', md[attr].data.days);
                 //$(aTd[i]).find('div > div > span.hours').text(md[attr].data.hours);
                 //$(aTd[i]).attr('hours', md[attr].data.hours);
                 $(aTd[i]).unbind().on('touchend', function () {
                 //_this.element.trigger('touchMonth', {month: $(this).attr('month'), days: $(this).attr('days'), hours: $(this).attr('hours')});
                 var m = $(this).attr('month') < 10 ? '0' + $(this).attr('month') : $(this).attr('month');
                 _this.element.trigger('touchMonth', {month: _this.option('currYear') + '-' + m});
                 });
                 }
                 }*/
            }
        },
        _setOption: function (key, value) {
            //console.log('_setOption: key=%s  value=%s', key, value);
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