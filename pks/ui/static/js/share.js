/**
 * SNS공유
 * app.share 정보를 활용 (image, url, text)
 */

//kakao init
var bInitKakao = false;
var kakaoJavascriptKey = '45828a631ac6ffb24c489e39bd0ac47b'; //kakao developer
$(document).ready(function(){
	if(!bInitKakao){
		try{
			Kakao.init(kakaoJavascriptKey);
			bInitKakao = true;
		}catch(e){
			alert(e);
		}
	}

  //  window.fbAsyncInit = function() {
  //     FB.init({
  //       appId      : '1036395799812464',
  //       xfbml      : true,
  //       version    : 'v2.8'
  //     });
  //     FB.AppEvents.logPageView();
  //   };

  //   (function(d, s, id){
  //      var js, fjs = d.getElementsByTagName(s)[0];
  //      if (d.getElementById(id)) {return;}
  //      js = d.createElement(s); js.id = id;
  //      js.src = "//connect.facebook.net/en_US/sdk.js";
  //      fjs.parentNode.insertBefore(js, fjs);
  //    }(document, 'script', 'facebook-jssdk'));

});
//kakao init @


function sendSns(sns, url, txt, img)
{
	var o;
	var _url = encodeURIComponent(url);
	var _txt = encodeURIComponent(txt);
	var _img = encodeURIComponent(img);
	var _br  = encodeURIComponent('\r\n');


	switch(sns)
	{
		case 'facebook':
			o = {
				method:'popup',
				url:'http://www.facebook.com/sharer/sharer.php?u=' + _url
			};
			break;
		case 'twitter':
			o = {
				method:'popup',
				url:'http://twitter.com/intent/tweet?text=' + _txt + '&url=' + _url
			};
			break;
		case 'kakaotalk':
			o = {
				method:'self'
			}
			Kakao.Link.sendTalkLink({
				label:txt + '\n'+ url
				,
				image:{
					src:img,
					width:300,
					height:300
				},
				webButton:{
					text:'PHOPL에서 보기',
					url:url
				},
				installTalk:false

			});
			break;
		case 'kakaostory':
			if( true ){
				o = {
					method:'web2app',
					param:'posting?post=' + _txt + _br + _url + '&apiver=1.0&appver=3.0', //&appid=dev.epiloum.net&appname=' + encodeURIComponent('Epiloum 개발노트'),
					a_store:'itms-apps://itunes.apple.com/app/id486244601?mt=8',
					g_store:'market://details?id=com.kakao.story',
					a_proto:'storylink://',
					g_proto:'scheme=kakaolink;package=com.kakao.story'
				};
			} else {
				//android etc.
				o = {
					method:'self'
				}
				Kakao.Story.share({
					text: txt,
					url: url
				});
			}
			break;
		case 'naverline':
			o = {
				method:'web2app',
				param:'msg/text/' + _txt + _br + _url,
				a_store:'itms-apps://itunes.apple.com/app/id443904275?mt=8',
				g_store:'market://details?id=jp.naver.line.android',
				a_proto:'line://',
				g_proto:'scheme=line;package=jp.naver.line.android'
			};
			break;
			case 'naverband':
			o = {
				method:'web2app',
				param:'create/post?text=' + _txt + _br + _url,
				a_store:'itms-apps://itunes.apple.com/app/id542613198?mt=8',
				g_store:'market://details?id=com.nhn.android.band',
				a_proto:'bandapp://',
				g_proto:'scheme=bandapp;package=com.nhn.android.band'
			};
			break;
		default:
			alert('지원하지 않는 SNS입니다.');
			return false;
	}

	switch(o.method)
	{
		case 'self':
			break;
		case 'popup':
			window.open(o.url);
			break;
		case 'web2app':
			if(navigator.userAgent.match(/android/i))
			{
				// Android
				setTimeout(function(){ location.href = 'intent://' + o.param + '#Intent;' + o.g_proto + ';end'}, 100);
			} else if(navigator.userAgent.match(/(iphone)|(ipod)|(ipad)/i)) {
				// Apple
				setTimeout(function(){ location.href = o.a_store; }, 4000);
				setTimeout(function(){ location.href = o.a_proto + o.param }, 100);
			} else {
				alert('Only support mobile.');
			}
		break;
	}
}
