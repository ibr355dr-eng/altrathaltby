(function(){
  "use strict";
  var D = window.MZ, H = D.humors, Q = D.questions, B = D.basics, K = ["d","s","b","k"];
  var QUAL = {h:["d","s"], c:["b","k"], w:["d","b"], y:["s","k"]};
  var QNAME = {h:"الحرارة", c:"البرودة", w:"الرطوبة", y:"اليبوسة"};
  var $ = function(s, r){ return (r||document).querySelector(s); };
  var ar = function(n){ return String(n).replace(/\d/g, function(c){ return "٠١٢٣٤٥٦٧٨٩"[c]; }); };
  var state = {sex:null, age:null, land:null, name:"", ans:[]};
  var step = -1;

  function pts(o){
    var p = {d:0,s:0,b:0,k:0};
    (o.q||[]).forEach(function(q){ QUAL[q].forEach(function(k){ p[k] += 1; }); });
    if (o.p) K.forEach(function(k){ p[k] += o.p[k]||0; });
    return p;
  }
  function ageBand(a){ return B.age.bands.find(function(b){ return a <= b.max; }); }
  function srcLinks(ids){
    return ids.map(function(id){
      var s = D.src[id];
      return '<a href="/mizaj/sources/#'+id+'">'+s.short+' ص'+s.page+'</a>';
    }).join("، ");
  }

  /* ---------- basics ---------- */
  function renderBasics(){
    var f = $("#mz-basics");
    function radios(name, opts){
      return opts.map(function(o,i){
        return '<label class="opt"><input type="radio" name="'+name+'" value="'+i+'"><span>'+o.t+'</span></label>';
      }).join("");
    }
    $("#mz-sex").innerHTML = radios("sex", B.sex.options);
    $("#mz-land").innerHTML = radios("land", B.land.options);
    f.addEventListener("input", checkBasics);
    f.addEventListener("submit", function(e){
      e.preventDefault();
      state.name = $("#mz-name").value.trim();
      state.sex = +f.sex.value; state.age = +$("#mz-age").value; state.land = +f.land.value;
      state.ans = new Array(Q.length).fill(null);
      go(0);
    });
  }
  function checkBasics(){
    var f = $("#mz-basics"), a = +$("#mz-age").value;
    $("#mz-start").disabled = !(f.sex.value !== "" && f.land.value !== "" && a >= 1 && a <= 120);
  }

  /* ---------- questions ---------- */
  function go(i){
    step = i;
    $("#mz-intro").classList.add("hidden");
    $("#mz-result").classList.add("hidden");
    $("#mz-q").classList.remove("hidden");
    var q = Q[i];
    $("#mz-qnum").textContent = "السؤال " + ar(i+1) + " من " + ar(Q.length);
    $("#mz-genus").textContent = q.genus;
    $("#mz-bar").style.width = (i / Q.length * 100) + "%";
    $("#mz-qt").textContent = q.t;
    $("#mz-opts").innerHTML = q.options.map(function(o,j){
      return '<label class="opt"><input type="radio" name="q" value="'+j+'"'+(state.ans[i]===j?" checked":"")+'><span>'+o.t+'</span></label>';
    }).join("");
    $("#mz-qsrc").innerHTML = "المصدر: " + srcLinks(q.src);
    $("#mz-prev").disabled = false;
    $("#mz-next").disabled = state.ans[i] === null;
    $("#mz-next").textContent = i === Q.length-1 ? "اعرض النتيجة" : "التالي";
    $("#mz-q h2").focus();
    window.scrollTo({top: $("#mz-app").offsetTop - 80, behavior: "smooth"});
  }
  function bindQ(){
    $("#mz-opts").addEventListener("change", function(e){
      state.ans[step] = +e.target.value;
      $("#mz-next").disabled = false;
    });
    $("#mz-next").addEventListener("click", function(){
      if (state.ans[step] === null) return;
      if (step < Q.length-1) go(step+1); else { save(); result(); }
    });
    $("#mz-prev").addEventListener("click", function(){
      if (step > 0) go(step-1);
      else { $("#mz-q").classList.add("hidden"); $("#mz-intro").classList.remove("hidden"); }
    });
  }

  /* ---------- scoring ---------- */
  function score(){
    var tot = {d:1,s:1,b:1,k:1}, why = [];
    function add(p, label, reason, src){
      var any = false;
      K.forEach(function(k){ tot[k] += p[k]||0; if (p[k]) any = true; });
      if (any && reason) why.push({label:label, reason:reason, src:src, p:p});
    }
    var sx = B.sex.options[state.sex], ab = ageBand(state.age), ld = B.land.options[state.land];
    add(sx.p, "الجنس: " + sx.t, sx.why, B.sex.src);
    add(ab.p, "العمر: " + ar(state.age) + " (" + ab.t + ")", ab.why, B.age.src);
    add(ld.p, "البلد: " + ld.t, ld.why, B.land.src);
    Q.forEach(function(q,i){
      var o = q.options[state.ans[i]];
      add(pts(o), q.genus + ": " + o.t, o.why, q.src);
    });
    var sum = K.reduce(function(a,k){ return a + tot[k]; }, 0);
    var raw = K.map(function(k){ return {k:k, v: tot[k]/sum*100}; });
    var fl = raw.map(function(r){ return {k:r.k, v:Math.floor(r.v), rem:r.v-Math.floor(r.v)}; });
    var left = 100 - fl.reduce(function(a,r){ return a + r.v; }, 0);
    fl.slice().sort(function(a,b){ return b.rem - a.rem; }).slice(0,left).forEach(function(r){ r.v++; });
    var pct = {}; fl.forEach(function(r){ pct[r.k] = r.v; });
    return {pct:pct, why:why, heat:(tot.d+tot.s)-(tot.b+tot.k), wet:(tot.d+tot.b)-(tot.s+tot.k)};
  }

  /* ---------- result ---------- */
  function result(){
    var r = score(), pct = r.pct;
    var order = K.slice().sort(function(a,b){ return pct[b]-pct[a]; });
    var top = order[0], second = order[1];
    $("#mz-q").classList.add("hidden");
    $("#mz-intro").classList.add("hidden");
    var R = $("#mz-result"); R.classList.remove("hidden");
    $("#mz-who").textContent = state.name ? ("نتيجة " + state.name) : "نتيجتك";
    $("#mz-bars").innerHTML = order.map(function(k){
      return '<div class="bar"><span class="nm" style="color:'+H[k].color+'">'+H[k].name+'</span>'+
        '<span class="tr" role="img" aria-label="'+H[k].name+' '+pct[k]+'٪"><i style="width:0;background:'+H[k].color+'" data-w="'+pct[k]+'"></i></span>'+
        '<span class="pc">'+ar(pct[k])+'٪</span></div>';
    }).join("");
    requestAnimationFrame(function(){ R.querySelectorAll(".tr i").forEach(function(i){ i.style.width = i.dataset.w + "%"; }); });
    var spread = pct[top] - pct[order[3]];
    var v;
    if (spread < 6) v = "مزاجك أقرب إلى <b>الاعتدال</b>، فلا يغلب عليه خلط ظاهر.";
    else if (pct[top] - pct[second] < 4) v = "الغالب عليك مزاج <b style=\"color:"+H[top].color+"\">"+H[top].name+"</b> يقاربه <b style=\"color:"+H[second].color+"\">"+H[second].name+"</b>.";
    else v = "الغالب عليك المزاج <b style=\"color:"+H[top].color+"\">ال"+H[top].name+"</b> ("+H[top].qual+").";
    $("#mz-verdict").innerHTML = v;
    var ql = [];
    ql.push(r.heat > 1 ? "الحرارة" : r.heat < -1 ? "البرودة" : "الاعتدال في الحر والبرد");
    ql.push(r.wet > 1 ? "الرطوبة" : r.wet < -1 ? "اليبوسة" : "الاعتدال في الرطوبة واليبوسة");
    $("#mz-qual").textContent = "الكيفيات الغالبة: " + ql.join("، و") + ".";
    $("#mz-desc").innerHTML = '<h3>علامات '+H[top].name+' المزاج في الكتب</h3><p>'+H[top].signs+'</p><p class="qsrc">المصدر: '+srcLinks(H[top].src)+'</p>';
    $("#mz-why").innerHTML = r.why.map(function(w){
      var tags = K.filter(function(k){ return w.p[k]; }).map(function(k){ return '<span class="tag" style="color:'+H[k].color+'">'+H[k].name+'</span>'; }).join(" ");
      return '<li><b>'+w.label+'</b> — '+w.reason+' '+tags+' <span class="src">('+srcLinks(w.src)+')</span></li>';
    }).join("");
    var rel = (D.related[top]||[]).concat(D.related.all||[]).filter(function(s){ return D.pub[s]; });
    $("#mz-rel-wrap").classList.toggle("hidden", !rel.length);
    $("#mz-rel").innerHTML = rel.map(function(s){
      return '<a class="card" href="/research/'+s+'/"><h3>'+D.pub[s].title+'</h3><p>'+D.pub[s].summary+'</p></a>';
    }).join("");
    $("#mz-share").onclick = function(){
      var txt = ($("#mz-who").textContent) + " في اختبار المزاج:\n" + order.map(function(k){ return H[k].name + " " + ar(pct[k]) + "٪"; }).join("، ") + "\n" + location.href;
      (navigator.share ? navigator.share({title:document.title, text:txt}) : navigator.clipboard.writeText(txt).then(function(){ $("#mz-share").textContent = "نُسخت النتيجة"; })).catch(function(){});
    };
    R.querySelector("h2").focus();
    window.scrollTo({top: $("#mz-app").offsetTop - 80, behavior: "smooth"});
  }

  /* ---------- shareable link: #r=sexIdx.age.landIdx.answers ---------- */
  function save(){
    var h = "r=" + state.sex + "." + state.age + "." + state.land + "." + state.ans.join("");
    history.replaceState(null, "", "#" + h);
  }
  function load(){
    var m = location.hash.match(/^#r=(\d)\.(\d{1,3})\.(\d)\.(\d+)$/);
    if (!m || m[4].length !== Q.length) return false;
    var a = m[4].split("").map(Number);
    if (a.some(function(x,i){ return x >= Q[i].options.length; })) return false;
    if (+m[1] >= B.sex.options.length || +m[3] >= B.land.options.length) return false;
    state = {sex:+m[1], age:+m[2], land:+m[3], name:"", ans:a};
    result(); return true;
  }

  renderBasics(); bindQ();
  $("#mz-again").addEventListener("click", function(){
    history.replaceState(null, "", location.pathname);
    $("#mz-result").classList.add("hidden"); $("#mz-intro").classList.remove("hidden");
  });
  $("#mz-print").addEventListener("click", function(){ window.print(); });
  load();
})();
