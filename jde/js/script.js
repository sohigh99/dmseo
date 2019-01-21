// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    document.getElementById("myBtn").style.display = "block";
  } else {
    document.getElementById("myBtn").style.display = "none";
  }
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
  document.body.scrollTop = 0; // For Safari
  document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}


  // var counter_list = [10,10000,10000];
  // var str_counter_0 = counter_list[0];
  // var str_counter_1 = counter_list[1];
  // var str_counter_2 = counter_list[2];
  // var display_str = "";
  // var display_div = document.getElementById("display_div_id");

  // function incrementCount(current_count){
  //   setInterval(function(){
  //     // clear count
  //     while (display_div.hasChildNodes()) {
  //         display_div.removeChild(display_div.lastChild);
  //     }
  //     str_counter_0++;
  //     if (str_counter_0 > 99) {
  //       str_counter_0 = 10; // reset count
  //       str_counter_1++;    // increase next count
  //     }
  //     if(str_counter_1>99999){
  //       str_counter_2++;
  //     }
  //     display_str = str_counter_2.toString() + str_counter_1.toString() + str_counter_0.toString();
  //     for (var i = 0; i < display_str.length; i++) {
  //       var new_span = document.createElement('span');
  //       new_span.className = 'num_tiles';
  //       new_span.innerText = display_str[i];
  //       display_div.appendChild(new_span);
  //     }
  //   },1000);
  // }

  incrementAndShowValue();

function incrementAndShowValue() {
  var value = getCookie("visitcounter") || 0;
  var newValue = ("00000" + (Number(value) + 1)).slice(-6);
  var container = document.getElementById("counterVisitor");
  String(newValue).split("").forEach(function(item, index) {
    container.children[index].innerHTML = item;
  });
  counter++;
  setCookie("visitcounter", counter);
}

function setCookie(name, value, days) {
  var expires = "";
  if (days) {
    var date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + value + expires + "; path=https://stacksnippets.net/js";
}

function getCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}


