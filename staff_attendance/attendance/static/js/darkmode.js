const options = {
  bottom: '20px', // default: '32px'
  right: '20px', // default: '32px'
  left: 'unset', // default: 'unset'
  time: '0.8s', // default: '0.3s'
  mixColor: '#fff', // default: '#fff'
  backgroundColor: '#e1e1d7',  // default: '#fff'
  buttonColorDark: '#100f2c',  // default: '#100f2c'
  buttonColorLight: '#fff', // default: '#fff'
  label: '🌓', // default: ''
  autoMatchOsTheme: true // default: true
}
  
function addDarkmodeWidget() {
  new Darkmode(options).showWidget();
}
window.addEventListener('load', addDarkmodeWidget);
