var ta = "@cit_okawa_excel ";
var formattedDate = Utilities.formatDate(new Date(), "GMT", "HHmmss");
var date = " #test" + formattedDate;

function front(){
  var res = Twitter.tweet(ta + "front" + date);
}

function right(){
  var res = Twitter.tweet(ta + "right" + date);  
}

function left(){
  var res = Twitter.tweet(ta + "left" + date);
}

function back(){
  var res = Twitter.tweet(ta + "back" + date);
}
