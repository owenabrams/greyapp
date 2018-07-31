window.addEventListener("load", function(){
    ar nodes = document.querySelectorAll("[data-parallax]");
      for(var i=0; i<nodes.length; i++){
          var children = nodes[i].children;
          for(var n=0; n<children.length; n++){
          children[n].setAttribute("data-index", n+2);
          }
          nodes[i].addEventListener("mousemove", function(e){
              var elms = this.children;
              for(var c=0; c<elms.length; c++){
              var divisor = parseInt(elms[c].getAttribute("data-index"));
              var startX = this.offsetWidth/4;
              var startY = this.offsetHeight/8;
              elms[c].style.left = startX-(((e.screenX/divisor)-e.clientX)/3)+"px";
              elms[c].style.top = startY-(((e.screenY/divisor)-e.clientY)/3)+"px";
              }
              });
  
      }
  });