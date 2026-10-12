/* VIDYA shared interactivity (progressive enhancement over Django backend) */
(function(){
  const $ = (s, c=document)=>c.querySelector(s);
  const $$ = (s, c=document)=>[...c.querySelectorAll(s)];

  // Toasts
  function toast(msg, type='info'){
    let box = $('#vidya-toasts');
    if(!box){ box=document.createElement('div'); box.id='vidya-toasts'; document.body.appendChild(box); }
    const el=document.createElement('div');
    el.className='vidya-toast '+type; el.textContent=msg;
    box.appendChild(el); setTimeout(()=>{el.style.opacity='0'; setTimeout(()=>el.remove(),300);}, 3800);
  }
  window.vidyaToast = toast;
  // Surface Django messages as toasts
  $$('.vidya-django-msg').forEach(m=>toast(m.textContent.trim(), m.dataset.tags||'info'));

  // Active nav: Home = top of catalog, Courses = #catalog or any /courses/... detail
  const path = location.pathname;
  const hash = location.hash || '';
  const homeLink = $('[data-nav-home]');
  const catalogLink = $('[data-nav-catalog]');
  if(homeLink && catalogLink && (path === '/' || path === '/courses/')){
    if(hash === '#catalog'){ catalogLink.classList.add('active'); }
    else if(path === '/courses/'){ homeLink.classList.add('active'); }
    else { homeLink.classList.add('active'); }
  }
  let bestLen = -1;
  const candidates = $$('[data-nav-match]').filter(a=>!a.hasAttribute('data-nav-home')&&!a.hasAttribute('data-nav-catalog')).map(a=>{
    const key=a.getAttribute('data-nav-match')||'';
    let match=false, len=-1;
    if(key.startsWith('exact:')){
      const exactKey=key.slice(6)||'/';
      match = (path===exactKey || (exactKey==='/courses/' && path==='/'));
      len = 10000 + exactKey.length;
    } else if(key && key !== '/' && path.startsWith(key)){
      match=true; len=key.length;
    } else if(key === '/' && path === '/'){
      match=true; len=1;
    }
    return {a, match, len};
  }).filter(c=>c.match);
  candidates.forEach(c=>{ if(c.len>bestLen) bestLen=c.len; });
  candidates.forEach(c=>{ if(c.len===bestLen) c.a.classList.add('active'); });
  // Any deeper /courses/<slug>/ or /courses/lessons/... page highlights Courses
  if(catalogLink && path.startsWith('/courses/') && path !== '/courses/' && hash !== '#catalog'){
    catalogLink.classList.add('active');
  }

  // Show/hide password + basic client validation
  $$('[data-toggle-password]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const input = document.querySelector(btn.getAttribute('data-toggle-password'));
      if(!input) return;
      input.type = input.type==='password' ? 'text' : 'password';
      btn.innerHTML = input.type==='password' ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
    });
  });
  $$('form[data-validate]').forEach(f=>{
    f.addEventListener('submit', e=>{
      let ok=true, first=null;
      $$('[required]', f).forEach(inp=>{
        const bad = !inp.value.trim() || (inp.type==='email' && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(inp.value));
        inp.classList.toggle('is-invalid', bad);
        if(bad){ ok=false; first=first||inp; }
      });
      const p1=$('[name="password1"],[name="password"]',f), p2=$('[name="password2"]',f);
      if(p1&&p2&&p1.value!==p2.value){ p2.classList.add('is-invalid'); toast('Passwords do not match.','error'); ok=false; }
      if(!ok){ e.preventDefault(); toast('Please fix the highlighted fields.','error'); (first||p2)?.focus(); }
    });
  });

  // Course catalog client-side quick filter (enhances server filter)
  const q = $('#vidya-course-search');
  if(q){
    q.addEventListener('input', ()=>{
      const term=q.value.toLowerCase();
      $$('#vidya-course-grid .vidya-card-wrap').forEach(card=>{
        card.style.display = card.textContent.toLowerCase().includes(term) ? '' : 'none';
      });
    });
  }
  $$('.category-pill[data-cat]').forEach(p=>{
    p.addEventListener('click', ()=>{
      $$('.category-pill').forEach(x=>x.classList.remove('active')); p.classList.add('active');
      const cat=p.dataset.cat.toLowerCase();
      $$('#vidya-course-grid .vidya-card-wrap').forEach(card=>{
        const c=(card.dataset.category||'').toLowerCase();
        card.style.display = (!cat || c.includes(cat)) ? '' : 'none';
      });
    });
  });

  // Demo purchase confirmation (real enrollment is server POST)
  $$('[data-purchase-demo]').forEach(b=>b.addEventListener('click', ()=>{
    toast('Demo checkout: no real payment is processed. Use Enroll to join via backend.','success');
  }));

  // Demo assignment feedback
  $$('[data-assignment-demo]').forEach(b=>b.addEventListener('click', ()=>{
    toast('Demo submission received! Your instructor will review it on the server.','success');
  }));

  // Lesson completion animation + reminder
  $$('.progress-bar[data-animated]').forEach(bar=>{
    const target=parseFloat(bar.dataset.progress||bar.style.width||'0');
    bar.style.width='0%'; requestAnimationFrame(()=>setTimeout(()=>bar.style.width=target+'%',150));
  });

  // Comments (client demo persisted in localStorage, keyed per lesson)
  const commentList=$('#vidya-comments'), commentForm=$('#vidya-comment-form');
  if(commentList&&commentForm){
    const key='vidya-comments-'+(commentForm.dataset.lesson||'general');
    const load=()=>{ try{return JSON.parse(localStorage.getItem(key)||'[]')}catch{return[]} };
    const save=(a)=>localStorage.setItem(key, JSON.stringify(a));
    const render=()=>{
      commentList.innerHTML='';
      const items=load();
      if(!items.length){ commentList.innerHTML='<p class="text-muted">No comments yet — be the first! (demo, stored in your browser)</p>'; return; }
      items.forEach(c=>{
        const d=document.createElement('div'); d.className='border rounded p-2 mb-2 bg-light';
        d.innerHTML='<strong></strong> <small class="text-muted"></small><div></div>';
        d.querySelector('strong').textContent=c.name; d.querySelector('small').textContent=c.at; d.querySelector('div').textContent=c.text;
        commentList.appendChild(d);
      });
    };
    render();
    commentForm.addEventListener('submit', e=>{
      e.preventDefault();
      const name=$('#c-name').value.trim()||'Learner', text=$('#c-text').value.trim();
      if(!text){ toast('Write a comment first.','error'); return; }
      const items=load(); items.unshift({name, text, at:new Date().toLocaleString()});
      save(items); $('#c-text').value=''; render(); toast('Comment added (demo, browser-only).','success');
    });
  }

  // Quiz engine (demo data injected via data-quiz-json; posts nothing to server)
  const quizRoot=$('#vidya-quiz');
  if(quizRoot){
    const questions=JSON.parse(quizRoot.dataset.quizJson||'[]');
    let idx=0, answers=Array(questions.length).fill(null), secs=parseInt(quizRoot.dataset.duration||'600',10);
    const qTitle=$('#q-title'), qOpts=$('#q-opts'), qCount=$('#q-count'), qTimer=$('#q-timer'), qPrev=$('#q-prev'), qNext=$('#q-next'), qResult=$('#q-result');
    const tick=()=>{ const m=String(Math.floor(secs/60)).padStart(2,'0'), s=String(secs%60).padStart(2,'0'); if(qTimer)qTimer.textContent=m+':'+s; if(secs<=0){finish();return;} secs--; };
    const timer=setInterval(tick,1000); tick();
    function renderQ(){
      const quest=questions[idx]; if(!quest) return;
      qCount.textContent=`Question ${idx+1} of ${questions.length}`;
      qTitle.textContent=quest.q;
      qOpts.innerHTML='';
      quest.options.forEach((op,i)=>{
        const d=document.createElement('div'); d.className='quiz-option mb-2'+(answers[idx]===i?' selected':'');
        d.textContent=op; d.addEventListener('click',()=>{answers[idx]=i; renderQ();}); qOpts.appendChild(d);
      });
      qPrev.disabled=idx===0; qNext.textContent=idx===questions.length-1?'Finish':'Next';
    }
    function finish(){
      clearInterval(timer);
      let score=0; questions.forEach((quest,i)=>{ if(answers[i]===quest.answer) score++; });
      quizRoot.querySelector('#q-body').style.display='none';
      qResult.style.display='block';
      qResult.innerHTML=`<h3>Your score: ${score} / ${questions.length}</h3><p class="text-muted">Demo quiz — scored in your browser, not saved to the server.</p><div class="progress mb-3"><div class="progress-bar" style="width:${(score/Math.max(questions.length,1))*100}%"></div></div><button class="btn btn-emerald" onclick="location.reload()">Retry</button> <a class="btn btn-outline-secondary" href="/quizzes/tests/">Back to tests</a>`;
      toast(`Quiz finished: ${score}/${questions.length}`,'success');
    }
    qPrev?.addEventListener('click',()=>{ if(idx>0){idx--; renderQ();} });
    qNext?.addEventListener('click',()=>{ if(idx<questions.length-1){idx++; renderQ();} else finish(); });
    renderQ();
  }

  // Certificate print
  $('#vidya-print-cert')?.addEventListener('click',()=>window.print());
  // Remember-me hint (Django session handles auth; this is UX only)
  const rm=$('#id_remember'); rm?.addEventListener('change',()=>toast(rm.checked?'We will keep you signed in on this browser (demo).':'You will be signed out when the browser closes (demo).'));
})();
