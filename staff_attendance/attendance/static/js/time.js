function twoDigit(num) {
  let base;
  if( num < 10 ) 
    base = '0' + num; 
  else 
    base = num; 
  return base;
}

function showClock() {
  let nowTime = new Date();
  let nowYear = twoDigit( nowTime.getFullYear() );
  let nowMonth = twoDigit( nowTime.getMonth() + 1 );
  let nowDate = twoDigit( nowTime.getDate() );
  let nowHour = twoDigit( nowTime.getHours() );
  let nowMin  = twoDigit( nowTime.getMinutes() );
  let nowSec  = twoDigit( nowTime.getSeconds() );

  let msg = nowYear + '.' + nowMonth + '.' + nowDate + ' ' + nowHour + ':' + nowMin + ':' + nowSec;
  document.getElementById('clock').innerHTML = msg;
}
setInterval('showClock()',1000);
