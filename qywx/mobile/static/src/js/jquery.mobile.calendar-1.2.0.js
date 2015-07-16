/*!
 * BJC Calendar plugin 1.2.0 for jQuery Mobile 1.4.5
 * Git HEAD hash: 68e55e78b292634d3991c795f06f5e37a512decc <> Date: Fri Oct 31 2014 17:33:30 UTC
 * http://www.billjc.com
 *
 * Copyright 2015, BJC, Inc.
 * Released under the MIT license.
 * http://jquery.org/license
 *
 */

(function ($) {

    $.widget('mobile.calendar', {
        initSelector: ":jqmData(role='calendar')",
        version: 'BJC Calendar plugin 1.2.0',

        options: {
            outLog: false, // 是否显示log
            prevNextMonthDaysVisible: false, // 显示上个月和下个月的天数
            weekNumber: ['日', '一', '二', '三', '四', '五', '六'],
            theme: null,// 主题
            mini: null, // 最小化样式
            mode: 'normal', // 分为：正常模式(normal)和周模式(week),暂无功能
            initDay: new Date(), // 显示当前月份日期
            startDay: '', // 开始日期
            endDay: '', // 结束日期
            data: {}, // 用于计算的所有数据 通过_calculate方式得来
            excludeDate: [], // 不能选取日期数组
            displayNl: true,
            confirmText: '确认',
            // statusDate: {s1: ['2015-5-25'], s2: ['2015-5-26'], s3: ['2015-5-27'], s4: ['2015-5-28']}, // 状态显示日期
            // s1 : 没有考勤记录， s2 ：有考勤记录，并且考勤正常，s3 ：有考勤记录，考勤异常， s4 ：有考勤记录，记录一半不完整
            selectedFn: function (ev, data) {
                //$(":jqmData(role='calendar')").trigger('selectedFn', data);
                $('.maskDiv').addClass('selectMonthBgAnimate');
                $('.dayConfrimDiv').addClass('dayConfrimDivAnimate');
                $('.dayConfrimDiv .selectedNum span').text(data.data.length);
            },
            selectedMonthFn: function (ev, data) {
                data._this.reload({initDay: data.data});
            },
            selectConfrimOk: function (ev, data) {
                //alert('你点的确定，你选了' + data.data.length + '天，可以在data.data里循环查看');
                data.c.trigger('selectConfrimOk', data);
            },
            selectConfrimCancel: function (ev, data) {
                data.c.calendar('selectConfrimCancel');
            }
        },

        selectConfrimCancel: function () {
            var maskDiv = $('.maskDiv').get(0);
            var dayConfrimDiv = $('.dayConfrimDiv').get(0);

            $(maskDiv).removeClass('selectMonthBgAnimate');
            $(dayConfrimDiv).removeClass('dayConfrimDivAnimate');
            this.element.find('table td.selected').removeClass('selected');
        },

        _calculate: function () {
            this._log('_calculate');

            var fdow = new Date(this.option('initDay').getFullYear(), this.option('initDay').getMonth(), 1).getDay();

            this._setOption('data', {
                //本月第一天星期几
                firstDayOfWeek: fdow,
                // 本月总天数
                totalDaysOfThisMonth: this._getTotalDays(this.option('initDay').getMonth() + 1, this.option('initDay').getFullYear()),
                // 上月总天数
                // totalDaysOfPrevMonth: this._getToalDaysOfPrevMonth(this.option('initDay').getMonth() + 1, this.option('initDay').getMonth() + 1),

                // 本月日历总共显示周数
                totalWeeksOfThisMonth: Math.ceil((fdow +
                    this._getTotalDays(this.option('initDay').getMonth() + 1, this.option('initDay').getFullYear())) / 7)
            });

        },

        _create: function (option) {
            this._log('_create');
            this._setOptions(option);
            // 数据校验
            if (this.option('weekNumber').length != 7) {
                console.error('parameters [weekNumber] error, please check it and run again.');
            }

            // initDay类型转换
            if (!(this.option('initDay') instanceof Date)) {
                try {
                    this._setOption('initDay', new Date(this.option('initDay')));
                } catch (e) {
                    console.error('parameters [initDay] error, it must be Data, please check it and run again.');
                }
            }

            //模式
            if (!this.option('mode').match(/normal|week/)) {
                console.error('parameters [mode] error, please check it and run again.');
                this._setOptions({mode: 'normal'});
            }

            this._calculate();
            this._buildHtml();
            this._initEvent();
        },

        _init: function (option) {
            this._log('_init');
            // initDay类型转换
            if (option && option['initDay'] && !(option['initDay'] instanceof Date)) {
                try {
                    this._setOption('initDay', new Date(option['initDay']));
                } catch (e) {
                    console.error('parameters [initDay] error, it must be Data, please check it and run again.');
                }
            }
            this._setOptions(option);
        },

        _formatTwo: function (num) {
            if (num < 10) return '0' + num;
            return num;
        },

        _buildHtml: function () {
            this._log('_buildHtml');
            var _this = this;
            var table = document.createElement('table');
            table.setAttribute("border", 0);
            // 标题caption ===========================================
            var caption = document.createElement('caption');

            var cLeftBtn = document.createElement('div');
            cLeftBtn.innerHTML = '<i class="left"></i><span style="vertical-align: middle;">'
                + this.option('initDay').getFullYear() + '</span><i class="right"></i>';
            var cLeftLeftBtn = document.createElement('div');
            var cLeftRightBtn = document.createElement('div');
            $(cLeftLeftBtn).on('touchend', function () {
                _this.option('initDay').setFullYear(_this.option('initDay').getFullYear() - 1);
                _this.reload({initDay: _this.option('initDay')});
            });
            cLeftBtn.appendChild(cLeftLeftBtn);
            $(cLeftRightBtn).on('touchend', function () {
                _this.option('initDay').setFullYear(_this.option('initDay').getFullYear() + 1);
                _this.reload({initDay: _this.option('initDay')});
            });
            cLeftBtn.appendChild(cLeftRightBtn);

            var title = document.createElement('div');
            title.innerHTML = '<span style="vertical-align: middle">' + (this.option('initDay').getMonth() + 1) + '月</span>&nbsp;<div class="jiantou" ></div>';
            title.style.marginLeft = '-2rem';
            $(title).on('touchend', function () {
                _this._displayMonthBar();
            });

            var cRightBtn = document.createElement('div');
            cRightBtn.innerHTML = '<span style="vertical-align: middle">今天</span>';
            $(cRightBtn).on('touchend', function () {
                _this.reload({initDay: new Date()});
            });
            if (this.option('initDay').getFullYear() == new Date().getFullYear() && this.option('initDay').getMonth() == new Date().getMonth()) {
                cRightBtn.style.visibility = 'hidden';
            }

            caption.appendChild(cLeftBtn);
            caption.appendChild(title);
            caption.appendChild(cRightBtn);
            table.appendChild(caption);

            // 星期thead ===========================================
            var wThead = document.createElement('thead');
            var wTr = document.createElement('tr');
            for (var i = 0, l = this.option('weekNumber').length; i < l; i++) {
                var th = document.createElement('th');
                th.setAttribute('scope', 'col');
                th.innerHTML = this.option('weekNumber')[i];
                if (i == 0 || i == 6) {
                    th.style.color = '#cccccc';
                }
                wTr.appendChild(th);
            }
            wThead.appendChild(wTr);
            table.appendChild(wThead);

            // 表体tbody ===========================================
            // 1. 循环当前表格所有天数
            var tbody = document.createElement('tbody');
            var ed = _this.option('excludeDate');
            var startTime = _this.options.startDay ? new Date(_this.options.startDay).getTime() : 0;
            var endTime = _this.options.endDay ? new Date(_this.options.endDay).getTime() : Number.MAX_VALUE;
            for (var i = 0, l = this.option('data').totalWeeksOfThisMonth; i < l; i++) {
                var tbodytr = document.createElement('tr');
                for (var ii = 0; ii < 7; ii++) {
                    var tbodytd = document.createElement('td');
                    if (ii == 0 || ii == 6) { //周末
                        tbodytd.className = 'week';
                    }
                    tbodytd.setAttribute('week', i);
                    tbodytd.setAttribute('day', ii + 1);
                    tbodytd.setAttribute('no', i * 7 + ii + 1);
                    tbodytd.setAttribute('date', _this.option('initDay').getFullYear() + '-' + _this._formatTwo(_this.option('initDay').getMonth() + 1) + '-' + _this._formatTwo(i * 7 + ii + 1 - _this.option('data').firstDayOfWeek));

                    // 判断当天是否排除选择
                    for (var iii = 0, lll = ed.length; iii < lll; iii++) {
                        var ta = ed[iii].split('-');
                        var tempDate = new Date();
                        tempDate.setYear(ta[0]);
                        tempDate.setMonth(ta[1] - 1);
                        tempDate.setDate(ta[2]);
                        if (!isNaN(tempDate.getFullYear())) {
                            if (tempDate.getFullYear() == _this.option('initDay').getFullYear()
                                && tempDate.getMonth() == _this.option('initDay').getMonth()
                                && tempDate.getDate() == (i * 7 + ii + 1 - _this.option('data').firstDayOfWeek)) {
                                //$(tbodytd).attr('exclude', 'true');
                                tbodytd.setAttribute('exclude', true);
                            }
                        }
                    }

                    // 是否超过开始或结束日期
                    if (_this.options.startDay && _this.options.endDay) {
                        if (!(new Date(tbodytd.getAttribute('date')).getTime() >= startTime &&
                            new Date(tbodytd.getAttribute('date')).getTime() <= endTime)) {
                            tbodytd.setAttribute('exclude', true);
                        }
                    } else if (_this.options.startDay) {
                        if (!(new Date(tbodytd.getAttribute('date')).getTime() >= startTime)) {
                            tbodytd.setAttribute('exclude', true);
                        }

                    } else if (_this.options.endDay) {
                        if (!(new Date(tbodytd.getAttribute('date')).getTime() <= endTime)) {
                            tbodytd.setAttribute('exclude', true);
                        }
                    }


                    // 判断当天
                    if (_this.option('initDay').getFullYear() == new Date().getFullYear() &&
                        _this.option('initDay').getMonth() == new Date().getMonth() &&
                        new Date().getDate() == (i * 7 + ii + 1 - _this.option('data').firstDayOfWeek)) {
                        tbodytd.setAttribute('today', true);
                        tbodytd.className = 'today';
                    }

                    _this._buildDayHtml(tbodytd);
                    tbodytr.appendChild(tbodytd);
                }

                // event start
                /*tbodytr.addEventListener('touchstart', function () {
                 for (var wi = 0, wl = this.children.length; wi < wl; wi++) {
                 this.children[wi].addEventListener('touchmove', function () {
                 this.className = 'selected';
                 }, false);
                 }
                 return false;
                 }, false);*/
                // event end

                tbody.appendChild(tbodytr);
            }
            table.appendChild(tbody);


            this.element.addClass('ui-calendar');
            this.element.append(table);

            var pnMonthBtn = document.createElement('div');
            pnMonthBtn.className = 'pnMonthBtn';
            var leftBtn = document.createElement('div');
            leftBtn.className = 'pnLeftBtn';
            leftBtn.innerHTML = '<i class="left"></i><span>上个月</span>';
            $(leftBtn).on('touchend', function () {
                _this.reload({initDay: _this._getPreMonth(_this.option('initDay'))});
            });
            var rightBtn = document.createElement('div');
            rightBtn.className = 'pnRightBtn';
            rightBtn.innerHTML = '<span>下个月</span><i class="right"></i>';
            $(rightBtn).on('touchend', function () {
                _this.reload({initDay: _this._getNextMonth(_this.option('initDay'))});
            });
            pnMonthBtn.appendChild(rightBtn);
            pnMonthBtn.appendChild(leftBtn);
            this.element.append(pnMonthBtn);

            // 加入遮罩
            var maskDiv = document.createElement('div');
            $(maskDiv).on('touchstart', function (e) {
                e.preventDefault();
                return false;
            });
            maskDiv.className = 'maskDiv';
            this.element.append(maskDiv);


            // 选择月份
            var monthDiv = document.createElement('div');
            monthDiv.className = 'displayMonthBar';
            var titleDiv = document.createElement('h4');
            titleDiv.innerHTML = '请选择月份';
            monthDiv.appendChild(titleDiv);

            _this._hiddenMonhDiv(maskDiv, monthDiv);

            for (var i = 1, l = 12; i <= 12; i++) {
                var mm = document.createElement('div');
                mm.innerHTML = i + '月';
                mm.setAttribute('month', i);
                if ((_this.option('initDay').getMonth() + 1) == i) {
                    $(mm).addClass('active');
                }
                $(mm).on('touchstart', function (ev) {
                    ev.preventDefault();
                });
                $(mm).on('touchend', function (ev) {
                    _this.option('initDay').setMonth(this.getAttribute('month') - 1);
                    _this._trigger('selectedMonthFn', ev, {_this: _this, data: _this.option('initDay')});
                });
                monthDiv.appendChild(mm);
            }
            this.element.append(monthDiv);

            // 天数选择确认框
            var dayConfrimDiv = document.createElement('div');
            dayConfrimDiv.className = 'dayConfrimDiv';
            var selectedNum = document.createElement('div');
            selectedNum.className = 'selectedNum';
            selectedNum.innerHTML = '已选<span></span>天';
            var btn = document.createElement('div');
            btn.className = 'btn';

            btn.innerHTML = '<div class="cancel">取消</div><div class="confrim">' + _this.option('confirmText') + '</div> ';

            dayConfrimDiv.appendChild(selectedNum);

            $(btn).find('.cancel').on('touchstart', function (ev) {
                ev.preventDefault();
            });
            $(btn).find('.confrim').on('touchstart', function (ev) {
                ev.preventDefault();
            });
            $(btn).find('.cancel').on('touchend', function (ev) {
                var data = [];
                var ori = $('.ui-calendar table td.selected');
                for (var xuyI = 0, l = $('.ui-calendar table td.selected').length; xuyI < l; xuyI++) {
                    data.push(ori[xuyI]);
                }
                _this._trigger('selectConfrimCancel', ev, {
                    /*hovered: $(e3.target || e3.srcElement),*/
                    data: data,
                    c: _this.element
                });
            });
            $(btn).find('.confrim').on('touchend', function (ev) {
                var data = [];
                var ori = _this.element.find('table td.selected');
                for (var xuyI = 0, l = $('.ui-calendar table td.selected').length; xuyI < l; xuyI++) {
                    data.push(ori[xuyI].getAttribute('date'));
                }
                _this._trigger('selectConfrimOk', ev, {
                    /*hovered: $(e3.target || e3.srcElement),*/
                    data: data,
                    c: _this.element
                });
            });
            dayConfrimDiv.appendChild(btn);
            _this._hiddenDayConfrimDiv(maskDiv, dayConfrimDiv);
            this.element.append(dayConfrimDiv);

            // tips加入
            var tips = document.createElement('div');
            tips.className = 'tips';
            var tipsLeft = document.createElement('div');
            tipsLeft.className = 'tipsLeft tipsbg';
            var tipsRight = document.createElement('div');
            tipsRight.className = 'tipsRight tipsbg';
            var tipsContent = document.createElement('div');
            tipsContent.className = 'tipsContent';
            var tipsContentImg = document.createElement('div');
            tipsContentImg.className = 'tipsContentImg';
            tips.appendChild(tipsLeft);
            tips.appendChild(tipsRight);
            tipsContent.appendChild(tipsContentImg);
            tips.appendChild(tipsContent);
            this.element.append(tips);
        },

        _hiddenDayConfrimDiv: function (maskDiv, dayConfrimDiv) {
            var _this = this;
            $(maskDiv).on('touchstart', function (ev) {
                ev.preventDefault();
            });
            $(maskDiv).on('touchend', function (ev) {
                //if (_this._getStyle(maskDiv, 'display') == 'block' && _this._getStyle(dayConfrimDiv, 'display') == 'block') {
                _this.selectConfrimCancel();
                //}
            });
        },

        _hiddenMonhDiv: function (maskDiv, monthDiv) {
            var _this = this;
            $(maskDiv).on('touchstart', function (ev) {
                ev.preventDefault();
            });
            $(maskDiv).on('touchend', function (ev) {
                if (_this._getStyle(maskDiv, 'display') == 'block' && _this._getStyle(monthDiv, 'display') == 'block') {
                    $(maskDiv).removeClass('selectMonthBgAnimate');
                    $(monthDiv).removeClass('selectMonthDivAnimate');
                }
            });
        },

        _buildDayHtml: function (td) {
            var no = parseInt(td.getAttribute('no'));
            var day = parseInt(td.getAttribute('day'));
            var week = parseInt(td.getAttribute('week'));
            var firstDayOfWeek = this.option('data').firstDayOfWeek; // 本月第一天星期 0开始
            var totalDaysOfThisMonth = this.option('data').totalDaysOfThisMonth; //本月总天数

            var ri = document.createElement('div'); // 公历和农历
            if (this.option('displayNl')) {
                ri.className = 'gn';
            } else {
                ri.className = 'gn big';
            }


            var text = document.createTextNode(parseInt(td.getAttribute('no')) - this.option('data').firstDayOfWeek); // 日期
            ri.appendChild(text);

            if (this.option('displayNl')) {
                var nori = document.createElement('span');
                nori.appendChild(
                    document.createTextNode(
                        GetLunarDay(this.option('initDay').getFullYear(),
                            this.option('initDay').getMonth() + 1,
                            no - firstDayOfWeek)
                    )
                );
                ri.appendChild(nori);
            }


            var status = document.createElement('div'); // 状态点
            // status.className = 'status';
            // ps: 因业务需这里要把status改成content，这个div里要放一些新东西，比如文字。
            status.className = 'content';

            // 显示status状态
            //var statusDate = this.option('statusDate');
//            for (var sn in statusDate) {
//                for (var i = 0, l = statusDate[sn].length; i < l; i++) {
//                    var tDate = new Date(statusDate[sn][i]);
//                    var tdDate = new Date(td.getAttribute('date'));
//
//                    if (!isNaN(tDate.getFullYear())) {
//                        if (tDate.getFullYear() == tdDate.getFullYear() && tDate.getMonth() == tdDate.getMonth() && tDate.getDate() == tdDate.getDate()) {
//                            status.className += ' ' + sn;
//                        }
//                    }
//                }
//            }

            if (no - firstDayOfWeek > 0 && no <= (totalDaysOfThisMonth + firstDayOfWeek)) {
                td.appendChild(ri);
                td.appendChild(status);
            }


        },

        _getByClass: function (parent, className) {
            var aObj = parent.getElementsByTagName('*');
            var aR = [];
            for (var i = 0, l = aObj.length; i < l; i++) {
                if (aObj[i].className == className) {
                    aR.push(aObj[i]);
                }
            }
            return aR;
        },

        _initTdEvent: function (table) {
            var _this = this;
            var aTd = table.getElementsByTagName('td');
            for (var i = 0, l = aTd.length; i < l; i++) {
                $(aTd[i]).on('selectday', (function (i) {
                    return function () {
                        if (aTd[i].children.length > 0) {
                            $(this).addClass('selected');
                        }
                    }
                })(i));
                $(aTd[i]).on('unselectday', (function (i) {
                    return function () {
                        if (aTd[i].children.length > 0) {
                            $(this).removeClass('selected');
                        }
                    }
                })(i));
            }
        },

        _clearAllTd: function (table) {
            var _this = this;
            var aTd = table.getElementsByTagName('td');
            for (var i = 0, l = aTd.length; i < l; i++) {
                $(aTd[i]).removeClass('selected');
            }
        },


        _initEvent: function () {
            this._log('_initEvent');
            var _this = this;

            $(document).on('touchstart touchmove', function (ev) {
                ev.preventDefault();
                return false;
            });

            var table = this._getByClass(document, 'ui-calendar')[0].getElementsByTagName('table')[0];
            _this._initTdEvent(table);
            var aRows = table.rows;
            for (var i = 1, l = aRows.length; i < l; i++) {
                $(aRows[i]).bind('touchstart', function (ev) {
                    //ev.preventDefault();
                    _this._clearAllTd(table);
                    var offsetHeadHeight = _this.element.closest('[data-role="page"]').find('.ui-header').height();
                    var offsetPadding = _this.element.closest('[data-role="page"]').find('.ui-content').css('padding') ? parseInt($('.ui-content').css('padding')) : 20;
                    var offsetFooterHeight = _this.element.closest('[data-role="page"]').find('.ui-footer').height();
                    var oEvent1 = ev.originalEvent.changedTouches[0];
                    var parentNode = this;
                    var iSpeedX = 0, iSpeedY = 0, iLastX = oEvent1.pageX, iLastY = oEvent1.pageY;

                    var isScrolling = void 0;

                    var scorllHeight = document.body.scrollTop ? document.body.scrollTop : document.documentElement.scrollTop;

                    //alert(scorllHeight);

                    var iPageWidth = document.documentElement.clientWidth;
                    var iPageHeight = document.documentElement.clientHeight;

                    //alert( iPageHeight + " " + document.body.scrollHeight);


                    // alert(scorllHeight);
                    // alert(oEvent1.pageY + " " + oEvent1.clientY);

                    // 创建一个选择框
                    var oSelectBox = document.createElement('div');
                    oSelectBox.className = 'selectBox';
                    oSelectBox.style.left = oEvent1.pageX + 'px';
                    oSelectBox.style.right = iPageWidth - oEvent1.pageX + 'px';
                    oSelectBox.style.top = oEvent1.pageY + 'px';
                    oSelectBox.style.bottom = iPageHeight - oEvent1.pageY + 'px';

                    oSelectBox.startPos = {x: oEvent1.pageX, y: oEvent1.pageY};
                    document.body.appendChild(oSelectBox);

                    $(document).bind('touchmove', function (ev) {
                        var oEvent2 = ev.originalEvent.changedTouches[0];

                        //console.log(ev2.originalEvent.targetTouches.length);
                        //当屏幕有多个touch或者页面被缩放过，就不执行move操作
                        //if (ev2.originalEvent.targetTouches.length > 1 ||
                        //ev2.originalEvent.scale && ev2.originalEvent.scale !== 1) return false;

                        if (oSelectBox.startPos.y < oEvent2.pageY && oSelectBox.startPos.x < oEvent2.pageX) { // 左上 to 右下
                            oSelectBox.style.top = oSelectBox.startPos.y + 'px';
                            oSelectBox.style.left = oSelectBox.startPos.x + 'px';
                            oSelectBox.style.right = '';
                            oSelectBox.style.bottom = '';
                        } else if (oSelectBox.startPos.y < oEvent2.pageY && oSelectBox.startPos.x > oEvent2.pageX) { // 右上 to 左下
                            oSelectBox.style.top = oSelectBox.startPos.y + 'px';
                            oSelectBox.style.right = iPageWidth - oSelectBox.startPos.x + 'px';
                            oSelectBox.style.left = '';
                            oSelectBox.style.bottom = '';
                        } else if (oSelectBox.startPos.y > oEvent2.pageY && oSelectBox.startPos.x < oEvent2.pageX) { //左下 to 右上
                            oSelectBox.style.bottom = iPageHeight - oEvent1.pageY + 'px';
                            oSelectBox.style.left = oSelectBox.startPos.x + 'px';
                            oSelectBox.style.top = '';
                            oSelectBox.style.right = '';
                        } else if (oSelectBox.startPos.y > oEvent2.pageY && oSelectBox.startPos.x > oEvent2.pageX) { // 右下 to 左上
                            oSelectBox.style.bottom = iPageHeight - oEvent1.pageY + 'px';
                            oSelectBox.style.right = iPageWidth - oSelectBox.startPos.x + 'px';
                            oSelectBox.style.top = '';
                            oSelectBox.style.left = '';
                        }

                        //判断速度
                        var tx = oEvent2.pageX;
                        var ty = oEvent2.pageY;
                        iSpeedX = tx - iLastX;
                        iLastX = tx;
                        iSpeedY = ty - iLastY;
                        iLastY = ty;

                        // selctBox change size
                        oSelectBox.style.width = Math.abs(oEvent2.pageX - oSelectBox.startPos.x) + 'px';
                        oSelectBox.style.height = Math.abs(oEvent2.pageY - oSelectBox.startPos.y) + 'px';

                        // isScrolling为1时，表示纵向滑动，0为横向滑动
                        if (isScrolling === void 0) {
                            isScrolling = (Math.abs(iSpeedX) >= Math.abs(iSpeedY)) ? 1 : 0;
                        }


                        if (isScrolling) { // 横向
                            _this._fnPZ(oSelectBox, parentNode, offsetHeadHeight, offsetPadding);
                            // 碰撞检测
                            $(document).bind('touchstart', function (e) {
                                e.preventDefault(); // 防iphone右滑回退
                            });
                            return false;
                        } else { // 纵向
                            $(oSelectBox).remove();
                            $(document).unbind('touchstart'); // 防止iphone右滑动回退
                            $(document).unbind('touchmove');
                            $(document).unbind('touchend');
                        }


                    });

                    $(document).bind('touchend', function (ev) {
                        var e3 = ev.originalEvent.changedTouches[0];
                        _this._fnPZ(oSelectBox, parentNode, offsetHeadHeight, offsetPadding);
                        $(oSelectBox).remove();
                        $(document).unbind('touchstart'); // 防止iphone右滑动回退
                        $(document).unbind('touchmove');
                        $(document).unbind('touchend');
                        _this._isTdSelect(function () {
                            var data = [];
                            var ori = $('.ui-calendar table td.selected');
                            for (var xuyI = 0, l = $('.ui-calendar table td.selected').length; xuyI < l; xuyI++) {
                                data.push(ori[xuyI].getAttribute("date"));
                            }
                            _this._trigger('selectedFn', e3, {/*hovered: $(e3.target || e3.srcElement),*/ data: data});
                            //_this._displayDownBar();
                        });

                    });
                    //return false;
                });
            }
        },

        _isTdSelect: function (yes, no) {
            if ($('div.ui-calendar table td.selected').length > 0) {
                if (yes) yes();
            } else {
                if (no) yes();
            }
        },

        _displayMonthBar: function (height) {
            $('.maskDiv').addClass('selectMonthBgAnimate');
            $('.displayMonthBar').addClass('selectMonthDivAnimate');
        },

        _displayDownBar: function (data) {
            this._isTdSelect(function () {
                /*if ($('.selectMonthDiv').height() == 0) {
                 $('.selectMonthDiv').removeClass('selectMonthDivAnimate');
                 $('.selectMonthDiv').height(0);
                 } else {
                 $('.selectMonthDiv').removeClass('selectMonthDivAnimate');
                 $('.selectMonthDiv').height(0);
                 }*/
                $('.selectMonthDiv').addClass('selectMonthDivAnimate');
            }, function () {
                $('.selectMonthDiv').hide();
            });
        },

        _fnPZ: function (selectBox, parentNode, offsetHeadHeight, offsetPadding) {
            this._log('_fnPZ');
            var l1 = selectBox.offsetLeft;
            var r1 = l1 + selectBox.offsetWidth;
            var t1 = selectBox.offsetTop;
            var b1 = t1 + selectBox.offsetHeight;
            var offsetValueHeight = offsetHeadHeight + offsetPadding;
            var offsetValueWidth = offsetPadding;

            /*var l2 = oTargetDiv.offsetLeft;
             var r2 = l2+oTargetDiv.offsetWidth;
             var t2 = oTargetDiv.offsetTop;
             var b2 = t2+oTargetDiv.offsetHeight;*/


            var oArr = parentNode.children;
            // 这里 coolpad 手机android 4.3会对column-count的元素的定位offsetLeft都为0。
            //$('#xuyi1 h3').text(parentNode.children.length);
            //$('#xuyi1 h3').text(oArr[2].offsetLeft + ' ' + oArr[2].offsetTop + ' ' + l1 + ' ' + r1 + ' ' + t1 + ' ' + b1);

            for (var i = 0, l = oArr.length; i < l; i++) {
                if (!oArr[i].getAttribute('exclude')) {
                    if (r1 < (i * oArr[i].offsetWidth + offsetValueWidth) ||
                        l1 > (i * oArr[i].offsetWidth + oArr[i].offsetWidth + offsetValueWidth) ||
                        b1 < oArr[i].offsetTop + offsetValueHeight ||
                        t1 > (oArr[i].offsetTop + oArr[i].offsetHeight + offsetValueHeight)) {
                        if (($(oArr[i]).attr('class') + "").indexOf('selected') != -1) {
                            $(oArr[i]).trigger('unselectday');
                        }
                    } else {
                        if (($(oArr[i]).attr('class') + "").indexOf('selected') == -1) {
                            $(oArr[i]).trigger('selectday');
                        }
                    }
                }
            }
        },

        refresh: function (option) {
        },

        reload: function (option) {
            this.element.html('');
            this._create(option);
            this.element.trigger('refresh', this.options);
        },
//
//        destory: function () {
//            $.Widget.prototype.destroy.call(this);
//            $(this.element).remove();
//        },

        _setOption: function (key, value) {
            this._log('_setOption: key=' + key + '  value=' + value);
            $.Widget.prototype._setOption.apply(this, arguments);
        },

        _setOptions: function (options) {
            var key;
            for (key in options) {
                this._setOption(key, options[key]);
            }
            return this;
        },

        _getPreMonth: function (date) {
            if (date.getMonth() == 0) {
                return new Date(date.getFullYear() - 1, 11, 1);
            } else {
                return new Date(date.getFullYear(), date.getMonth() - 1, 1);
            }
        },

        _getNextMonth: function (date) {
            if (date.getMonth() == 11) {
                return new Date(date.getFullYear() + 1, 0, 1);
            } else {
                return new Date(date.getFullYear(), date.getMonth() + 1, 1);
            }
        },
        // 计算样式
        _getStyle: function (obj, attr) { // 建议使用此函数代替offsetWidth/height
            if (obj.currentStyle) {
                return obj.currentStyle[attr]; // ie
            } else {
                return getComputedStyle(obj, false)[attr];
            }
        },

        //计算指定月的总天数
        _getTotalDays: function (month, year) {
            if (month == 2) {
                if (this._isLeapYear(year)) {
                    return 29;
                }
                else {
                    return 28;
                }
            }
            else if (month == 4 || month == 6 || month == 9 || month == 11) {
                return 30;
            }
            else {
                return 31;
            }
        },
        _getToalDaysOfPrevMonth: function (month, year) {
            if (month == 1) {
                month = 12;
                year = year - 1;
            }
            else {
                month = month - 1;
            }
            return this._getTotalDays(month, year);
        },
//判断是否是闰年
        _isLeapYear: function (year) {
            return year % 400 == 0 || (year % 4 == 0 && year % 100 != 0);
        },


        _log: function (str) {
            if (this.option('outLog'))
                console.log(this.version + ' [' + str + ']');
        },

        empty: function () {
        }
    })
    ;
})
(jQuery);