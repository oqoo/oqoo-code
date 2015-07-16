/**
 * Created by Administrator on 2015/7/6.
 */
(function ($) {
	$.widget("mobile.loader", $.mobile.loader, {
		defaultHtml: "<div class='ui-loader'>" +				
			"<span class='ui-icon-loading'></span>" +
			"<h1></h1></div>",
			
		maskHtml:"<i style='background:#000;opacity:.18;width:"+document.documentElement.clientWidth+
			"px;height:"+document.documentElement.clientHeight+"px;position:absolute;top:0;left:0;margin-left:"+
			(-document.documentElement.clientWidth/2+10*2.75+1)+"px;top:"+
			(-document.documentElement.clientHeight/2+10*2.75+1)+"px;z-index:-1'></i>",
			
		show: function(theme, msgText, textonly) {
			this._super(theme, msgText, textonly);
			if (theme && theme.html) {
				this.element.css('opacity', 1);
			}
			this.element.append(this.maskHtml);
			//$(this.defaultHtml).append(this.maskHtml)
		}
	});
})(jQuery);