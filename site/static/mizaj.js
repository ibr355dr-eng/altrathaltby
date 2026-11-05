(function(){
  "use strict";
  var D = window.MZ, H = D.humors, Q = D.questions, B = D.basics, K = ["d","s","b","k"];
  var QUAL = {h:["d","s"], c:["b","k"], w:["d","b"], y:["s","k"]};
  var $ = function(s){ return document.querySelector(s); };
  var ar = function(n){ return String(n).replace(/\d/g, function(c){ return "٠١٢٣٤٥٦٧٨٩"[c]; }); };
  var state, step;

  function radios(name, opts){
    return opts.map(function(o,i){
      return '<label class="opt"><input type="radio" name="'+name+'" value="'+i+'"><span>'+o.t+'</span></label>';
    }).join("");
  }
  function show(id){
    ["mz-intro","mz-q","mz-result"].forEach(function(x){ $("#"+x).classList.toggle("hidden", x !== id); });
    var h = $("#"+id+" h2"); if (h) h.focus({preventScroll:true});
    window.scrollTo({top: $("#mz-app").offsetTop - 90, behavior: "smooth"});
  }

  /* البيانات الأساسية */
  $("#mz-sex").innerHTML = radios("sex", B.sex.options);
  $("#mz-land").innerHTML = radios("land", B.land.options);
  var form = $("#mz-basics");
  form.addEventListener("input", function(){
    var a = +$("#mz-age").value;
    $("#mz-start").disabled = !(form.sex.value !== "" && form.land.value !== "" && a >= 1 && a <= 120);
  });
  form.addEventListener("submit", function(e){
    e.preventDefault();
    state = {sex:+form.sex.value, age:+$("#mz-age").value, land:+form.land.value, ans:new Array(Q.length).fill(null)};
    go(0);
  });

  /* الأسئلة: الاختيار ينقل إلى السؤال التالي */
  function go(i){
    step = i;
    $("#mz-qnum").textContent = ar(i+1) + " / " + ar(Q.length);
    $("#mz-bar").style.width = (i / Q.length * 100) + "%";
    $("#mz-qt").textContent = Q[i].t;
    $("#mz-opts").innerHTML = radios("q", Q[i].options);
    if (state.ans[i] !== null) $("#mz-opts").querySelectorAll("input")[state.ans[i]].checked = true;
    show("mz-q");
  }
  $("#mz-opts").addEventListener("change", function(e){
    state.ans[step] = +e.target.value;
    setTimeout(function(){ step < Q.length-1 ? go(step+1) : result(); }, 220);
  });
  $("#mz-prev").addEventListener("click", function(){ step > 0 ? go(step-1) : show("mz-intro"); });

  /* الحساب */
  function score(){
    var t = {d:1,s:1,b:1,k:1};
    function add(o){
      (o.q||[]).forEach(function(q){ QUAL[q].forEach(function(k){ t[k] += 1; }); });
      K.forEach(function(k){ t[k] += (o.p && o.p[k]) || 0; });
    }
    add(B.sex.options[state.sex]);
    add(B.age.bands.find(function(b){ return state.age <= b.max; }));
    add(B.land.options[state.land]);
    Q.forEach(function(q,i){ add(q.options[state.ans[i]]); });
    var sum = K.reduce(function(a,k){ return a + t[k]; }, 0);
    var fl = K.map(function(k){ var v = t[k]/sum*100; return {k:k, v:Math.floor(v), r:v-Math.floor(v)}; });
    var left = 100 - fl.reduce(function(a,x){ return a + x.v; }, 0);
    fl.slice().sort(function(a,b){ return b.r - a.r; }).slice(0,left).forEach(function(x){ x.v++; });
    var pct = {}; fl.forEach(function(x){ pct[x.k] = x.v; });
    return pct;
  }

  /* النتيجة */
  function result(){
    history.replaceState(null, "", "#r=" + [state.sex, state.age, state.land, state.ans.join("")].join("."));
    var pct = score();
    var order = K.slice().sort(function(a,b){ return pct[b]-pct[a]; }), top = H[order[0]];
    $("#mz-name").textContent = top.name;
    $("#mz-name").style.color = top.color;
    $("#mz-qual").textContent = top.qual;
    $("#mz-text").textContent = top.text;
    $("#mz-bars").innerHTML = order.map(function(k){
      return '<div class="bar"><span>'+H[k].name+'</span><span class="tr"><i style="background:'+H[k].color+'" data-w="'+pct[k]+'"></i></span><b>'+ar(pct[k])+'٪</b></div>';
    }).join("");
    show("mz-result");
    requestAnimationFrame(function(){ document.querySelectorAll("#mz-bars i").forEach(function(i){ i.style.width = i.dataset.w + "%"; }); });
    var summary = order.map(function(k){ return H[k].name + " " + pct[k] + "%"; }).join("، ");
    var wa = $("#mz-wa");
    if (wa) wa.href = "https://wa.me/" + D.whatsapp + "?text=" + encodeURIComponent(D.waMsg + "\nنتيجتي: " + summary);
    $("#mz-share").onclick = function(){
      var txt = "نتيجتي في اختبار المزاج: " + summary + "\n" + location.href;
      var p = navigator.share ? navigator.share({text: txt}) : navigator.clipboard.writeText(txt).then(function(){ $("#mz-share").textContent = "نُسخ الرابط"; });
      p.catch(function(){});
    };
  }
  $("#mz-again").addEventListener("click", function(){
    history.replaceState(null, "", location.pathname);
    form.reset(); $("#mz-start").disabled = true; show("mz-intro");
  });

  /* فتح نتيجة من رابط مشاركة */
  var m = location.hash.match(/^#r=(\d)\.(\d{1,3})\.(\d)\.(\d+)$/);
  if (m && m[4].length === Q.length && +m[1] < B.sex.options.length && +m[3] < B.land.options.length) {
    var a = m[4].split("").map(Number);
    if (a.every(function(x,i){ return x < Q[i].options.length; })) {
      state = {sex:+m[1], age:+m[2], land:+m[3], ans:a};
      result();
    }
  }
})();
