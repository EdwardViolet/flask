//Ajax获取时间
function get_time(){
	$.ajax({
		url:"/time",
		timeout:10000,//超时设置10秒(单位毫秒)
		success:function(data){
			$("#time").html(data)
		},
		error:function(xhr,type,errorThrown){

		}
	});
}
setTimeout("javascript:location.href='../static/index.html'", 3000);
//window.location.href='../static/index.html';
setInterval(get_time,1000)