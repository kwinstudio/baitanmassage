const cmsTreatments = Array.isArray(window.BAITAN_TREATMENTS) ? window.BAITAN_TREATMENTS : [];
const siteConfig = window.BAITAN_SITE || {};
const apiBase = String(siteConfig?.booking?.apiBase || '').replace(/\/$/, '');
const services = Object.fromEntries(cmsTreatments.map(t => [t.id, {
  name: t.name,
  options: (t.durations || []).map(d => [`${d.minutes} minuten`, `€${Number(d.price).toLocaleString('nl-NL')}`, Number(d.minutes)])
}]));

const serviceSelect=document.querySelector('#serviceSelect');
const durationGrid=document.querySelector('#durationGrid');
const summary=document.querySelector('#bookingSummary');
const summaryService=document.querySelector('#summaryService');
const summaryChoice=document.querySelector('#summaryChoice');
const continueButton=document.querySelector('#bookButton');
const bookingStepDate=document.querySelector('#bookingStepDate');
const bookingDate=document.querySelector('#bookingDate');
const slotsGrid=document.querySelector('#slotsGrid');
const bookingStepDetails=document.querySelector('#bookingStepDetails');
const bookingForm=document.querySelector('#bookingForm');
const selectedTimeText=document.querySelector('#selectedTimeText');
const bookingConfirmation=document.querySelector('#bookingConfirmation');
const confirmationText=document.querySelector('#confirmationText');
const bookingError=document.querySelector('#bookingError');
let currentDuration=null;
let selectedTime=null;

function todayISO(){const d=new Date(); const off=d.getTimezoneOffset(); return new Date(d.getTime()-off*60000).toISOString().slice(0,10);}
function setError(msg=''){if(!bookingError)return; bookingError.textContent=msg; bookingError.hidden=!msg;}
function reveal(el){if(el){el.hidden=false; requestAnimationFrame(()=>el.classList.add('is-visible'));}}
function hide(el){if(el){el.hidden=true; el.classList.remove('is-visible');}}

function renderDurations(key){
  if(!durationGrid) return;
  durationGrid.innerHTML=''; currentDuration=null; selectedTime=null;
  hide(bookingStepDate); hide(bookingStepDetails); hide(bookingConfirmation); setError('');
  const item=services[key];
  if(!item){durationGrid.innerHTML='<p>Kies eerst een behandeling.</p>';summary.hidden=true;continueButton.disabled=true;continueButton.setAttribute('aria-disabled','true');return;}
  item.options.forEach(([duration,price,minutes])=>{
    const btn=document.createElement('button');btn.type='button';btn.className='duration-option';btn.innerHTML=`<span class="minutes">${duration}</span><span class="price">${price}</span>`;
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.duration-option').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active'); currentDuration={duration,price,minutes};
      summary.hidden=false;summaryService.textContent=item.name;summaryChoice.textContent=`${duration} · ${price}`;
      continueButton.disabled=false;continueButton.removeAttribute('aria-disabled');
    });
    durationGrid.appendChild(btn);
  });
  summary.hidden=true;continueButton.disabled=true;continueButton.setAttribute('aria-disabled','true');
}

async function apiFetch(url, options={}){
  const target = /^https?:\/\//i.test(url) ? url : `${apiBase}${url}`;
  const res=await fetch(target,{headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
  const data=await res.json().catch(()=>({}));
  if(!res.ok) throw new Error(data.error||'Er ging iets mis');
  return data;
}

async function loadSlots(){
  selectedTime=null; hide(bookingStepDetails); setError('');
  if(!bookingDate.value||!currentDuration||!serviceSelect.value)return;
  slotsGrid.innerHTML='<p class="slot-loading">Beschikbaarheid laden…</p>';
  let slots=[];
  try{const data=await apiFetch(`/api/availability?service=${encodeURIComponent(serviceSelect.value)}&duration=${currentDuration.minutes}&date=${bookingDate.value}`); slots=data.slots||[];}
  catch{slotsGrid.innerHTML='<p class="empty-state">Online reserveren is tijdelijk niet beschikbaar. Bel Baitan via 06 83 936 366.</p>'; return;}
  slotsGrid.innerHTML='';
  if(!slots.length){slotsGrid.innerHTML='<p class="empty-state">Geen vrije tijden op deze datum. Kies een andere dag.</p>';return;}
  slots.forEach(t=>{const b=document.createElement('button');b.type='button';b.className='slot';b.textContent=t;b.addEventListener('click',()=>{document.querySelectorAll('.slot').forEach(x=>x.classList.remove('active'));b.classList.add('active');selectedTime=t;selectedTimeText.textContent=`${bookingDate.value.split('-').reverse().join('-')} om ${t}`;reveal(bookingStepDetails);bookingStepDetails.scrollIntoView({behavior:'smooth',block:'nearest'});});slotsGrid.appendChild(b);});
}

if(serviceSelect)serviceSelect.addEventListener('change',e=>renderDurations(e.target.value));
if(continueButton)continueButton.addEventListener('click',()=>{if(!currentDuration||!serviceSelect.value)return; bookingDate.min=todayISO(); if(!bookingDate.value)bookingDate.value=todayISO(); reveal(bookingStepDate); loadSlots(); bookingStepDate.scrollIntoView({behavior:'smooth',block:'nearest'});});
if(bookingDate)bookingDate.addEventListener('change',loadSlots);

if(bookingForm)bookingForm.addEventListener('submit',async e=>{
  e.preventDefault(); setError('');
  if(!selectedTime||!currentDuration||!serviceSelect.value)return setError('Kies eerst een tijdstip.');
  const fd=new FormData(bookingForm); const payload={service:serviceSelect.value,duration:currentDuration.minutes,date:bookingDate.value,time:selectedTime,name:fd.get('name'),email:fd.get('email'),phone:fd.get('phone'),notes:fd.get('notes')||''};
  const submit=bookingForm.querySelector('button[type="submit"]'); submit.disabled=true; submit.textContent='Reservering bevestigen…';
  try{
    const data=await apiFetch('/api/appointments',{method:'POST',body:JSON.stringify(payload)});
    const dateText=payload.date.split('-').reverse().join('-');
    confirmationText.innerHTML=`<strong>${data.service_name}</strong><br>${payload.duration} minuten · ${currentDuration.price}<br>${dateText} om ${payload.time}<br><br>Reserveringsnummer: <strong>${data.code}</strong>`;
    hide(bookingStepDetails); reveal(bookingConfirmation); bookingConfirmation.scrollIntoView({behavior:'smooth',block:'center'}); bookingForm.reset();
  }catch(err){setError(err.message); if(/niet meer beschikbaar|bezet/.test(err.message))loadSlots();}
  finally{submit.disabled=false;submit.textContent='Bevestig reservering';}
});

document.querySelectorAll('[data-service]').forEach(link=>link.addEventListener('click',()=>{const key=link.dataset.service;if(serviceSelect&&services[key]){serviceSelect.value=key;renderDurations(key);setTimeout(()=>document.querySelector('#boeken')?.scrollIntoView({behavior:'smooth'}),10);}}));

document.querySelectorAll('.faq-question').forEach(btn=>btn.addEventListener('click',()=>{const item=btn.closest('.faq-item');const open=item.classList.toggle('open');btn.setAttribute('aria-expanded',String(open));}));
const menuToggle=document.querySelector('.menu-toggle');const navLinks=document.querySelector('.nav-links');
if(menuToggle&&navLinks){menuToggle.addEventListener('click',()=>{const open=navLinks.classList.toggle('open');document.body.classList.toggle('nav-open',open);menuToggle.setAttribute('aria-expanded',String(open));});navLinks.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{navLinks.classList.remove('open');document.body.classList.remove('nav-open');menuToggle.setAttribute('aria-expanded','false');}));}

const mobileBook=document.querySelector('.mobile-book');
const bookingSection=document.querySelector('#boeken');
let bookingVisible=false;
function updateMobileBook(){
  if(!mobileBook)return;
  const scrolled=window.scrollY>420;
  mobileBook.classList.toggle('is-hidden',!scrolled||bookingVisible);
}
if(mobileBook){
  mobileBook.classList.add('is-hidden');
  window.addEventListener('scroll',updateMobileBook,{passive:true});
  updateMobileBook();
}
if(mobileBook&&bookingSection&&'IntersectionObserver' in window){
  const mobileBookObserver=new IntersectionObserver(entries=>{
    bookingVisible=entries[0].isIntersecting&&entries[0].intersectionRatio>.08;
    updateMobileBook();
  },{threshold:[0,.08,.2]});
  mobileBookObserver.observe(bookingSection);
}


// Privacy-friendly Google Maps: load only after explicit click.
document.querySelectorAll('.load-map').forEach(button=>{
  button.addEventListener('click',()=>{
    const shell=button.closest('.map-consent');
    const src=shell?.dataset.mapUrl;
    if(!shell||!src)return;
    const iframe=document.createElement('iframe');
    iframe.className='map';
    iframe.title='Kaart van Baitan Thai Massage';
    iframe.loading='lazy';
    iframe.referrerPolicy='no-referrer-when-downgrade';
    iframe.src=src;
    shell.replaceWith(iframe);
  });
});

// Five-question massage choice helper.
const choiceShell=document.querySelector('.choice-shell');
if(choiceShell){
  const questions=[...choiceShell.querySelectorAll('.choice-question')];
  const result=choiceShell.querySelector('#choiceResult');
  const progressText=choiceShell.querySelector('#choiceProgressText');
  const progressBar=choiceShell.querySelector('#choiceProgressBar');
  const resultTitle=choiceShell.querySelector('#choiceResultTitle');
  const resultText=choiceShell.querySelector('#choiceResultText');
  const resultBook=choiceShell.querySelector('#choiceResultBook');
  const resultDetail=choiceShell.querySelector('#choiceResultDetail');
  const restart=choiceShell.querySelector('#choiceRestart');
  let step=0;
  let scores={thai:0,aroma:0,sport:0,hotstone:0,duo:0};

  const messages={
    thai:'Traditionele Thaise technieken met warme, geurloze olie.',
    aroma:'Thaise oliemassage met een geur naar keuze.',
    sport:'Sportmassage uit het actuele behandelaanbod van Baitan.',
    hotstone:'Massage met warme stenen.',
    duo:'Samen genieten van een massage bij Baitan.'
  };

  function treatmentFor(id){return cmsTreatments.find(t=>t.id===id);}
  function showStep(index){
    questions.forEach((q,i)=>q.hidden=i!==index);
    if(progressText)progressText.textContent=`Vraag ${Math.min(index+1,5)} van 5`;
    if(progressBar)progressBar.style.width=`${Math.min((index/5)*100,100)}%`;
  }
  function finish(){
    questions.forEach(q=>q.hidden=true);
    if(progressText)progressText.textContent='Je resultaat';
    if(progressBar)progressBar.style.width='100%';
    const best=Object.entries(scores).sort((a,b)=>b[1]-a[1])[0]?.[0]||'thai';
    const t=treatmentFor(best);
    if(resultTitle)resultTitle.textContent=t?.name||'Thaise massage';
    if(resultText)resultText.textContent=messages[best]||'Bekijk deze behandeling bij Baitan.';
    if(resultDetail)resultDetail.href=t?.slug?`/${t.slug}`:'/massages';
    if(resultBook){
      const salonized=siteConfig?.booking?.provider==='salonized' ? siteConfig?.booking?.salonizedBookingUrl : '';
      if(salonized){
        resultBook.href=salonized;
        resultBook.target='_blank';
        resultBook.rel='noopener';
      }else{
        resultBook.dataset.service=best;
        resultBook.href='#boeken';
        resultBook.addEventListener('click',()=>{
          if(serviceSelect&&services[best]){
            serviceSelect.value=best;
            renderDurations(best);
          }
        },{once:true});
      }
    }
    if(result)result.hidden=false;
  }
  questions.forEach((q,index)=>{
    q.querySelectorAll('.choice-option').forEach(btn=>btn.addEventListener('click',()=>{
      const score=btn.dataset.score;
      if(score==='neutral'){
        Object.keys(scores).forEach(k=>scores[k]+=0.2);
      }else if(scores[score]!==undefined){
        scores[score]+=2;
      }
      if(index===4){finish();}
      else{step=index+1;showStep(step);}
    }));
  });
  restart?.addEventListener('click',()=>{
    scores={thai:0,aroma:0,sport:0,hotstone:0,duo:0};
    step=0;
    if(result)result.hidden=true;
    showStep(0);
  });
  showStep(0);
}


// Salonized is the active booking destination: make the floating CTA direct.
if(mobileBook && siteConfig?.booking?.provider==='salonized' && siteConfig?.booking?.salonizedBookingUrl){
  mobileBook.href=siteConfig.booking.salonizedBookingUrl;
  mobileBook.target='_blank';
  mobileBook.rel='noopener';
}

// Treatment detail modal. Links remain normal SEO links without JavaScript.
const treatmentDialog=document.querySelector('#treatmentDialog');
if(treatmentDialog){
  const dialogImage=treatmentDialog.querySelector('#treatmentDialogImage');
  const dialogLabel=treatmentDialog.querySelector('#treatmentDialogLabel');
  const dialogTitle=treatmentDialog.querySelector('#treatmentDialogTitle');
  const dialogText=treatmentDialog.querySelector('#treatmentDialogText');
  const dialogFeatures=treatmentDialog.querySelector('#treatmentDialogFeatures');
  const dialogPrices=treatmentDialog.querySelector('#treatmentDialogPrices');
  const dialogBook=treatmentDialog.querySelector('#treatmentDialogBook');
  const dialogPage=treatmentDialog.querySelector('#treatmentDialogPage');

  function openTreatment(id){
    const t=cmsTreatments.find(item=>item.id===id);
    if(!t)return;
    dialogTitle.textContent=t.name||'Behandeling';
    dialogText.textContent=t.detailText||t.description||'';
    dialogImage.src=t.image||siteConfig?.hero?.image||'';
    dialogImage.alt=t.imageAlt||t.name||'Massagebehandeling';
    dialogLabel.textContent=t.imageLabel||'';
    dialogLabel.hidden=!t.imageLabel;
    dialogFeatures.innerHTML=(t.features||[]).map(x=>`<li>${x}</li>`).join('');
    dialogPrices.innerHTML=(t.durations||[]).map(d=>`<span><strong>${d.minutes} min</strong> €${Number(d.price).toLocaleString('nl-NL')}</span>`).join('');
    dialogPage.href=t.slug?`/${t.slug}`:'/massages';
    const salonized=siteConfig?.booking?.provider==='salonized' ? siteConfig?.booking?.salonizedBookingUrl : '';
    dialogBook.href=salonized||'#boeken';
    if(salonized){dialogBook.target='_blank';dialogBook.rel='noopener';}
    else{dialogBook.removeAttribute('target');dialogBook.removeAttribute('rel');}
    if(typeof treatmentDialog.showModal==='function')treatmentDialog.showModal();
    else treatmentDialog.setAttribute('open','');
  }

  document.querySelectorAll('[data-treatment-modal]').forEach(link=>{
    link.addEventListener('click',e=>{
      e.preventDefault();
      openTreatment(link.dataset.treatmentModal);
    });
  });
}

// Legal footer modal.
const legalDialog=document.querySelector('#legalDialog');
if(legalDialog){
  const title=legalDialog.querySelector('#legalDialogTitle');
  const body=legalDialog.querySelector('#legalDialogBody');
  const link=legalDialog.querySelector('#legalDialogLink');
  const legalContent={
    terms:{
      title:'Algemene voorwaarden',
      html:'<p>De voorwaarden van Baitan gelden voor diensten, boekingen, betalingen, annuleringen en gedrag in de salon.</p>',
      href:'/voorwaarden'
    },
    privacy:{
      title:'Privacy & cookies',
      html:'<p>De website gebruikt de gegevens die nodig zijn voor contact en verwijst voor online boeken naar Salonized. Google Maps wordt pas na jouw keuze geladen.</p>',
      href:'/privacy'
    },
    cancel:{
      title:'Annuleren & afspraken',
      html:'<p>Kosteloos annuleren kan tot 24 uur vóór de afspraak. Binnen 24 uur vindt volgens de gepubliceerde voorwaarden geen restitutie plaats. Bij te laat komen kan de behandeltijd worden ingekort.</p>',
      href:'/voorwaarden'
    },
    business:{
      title:'Bedrijfsgegevens',
      html:`<p><strong>${siteConfig.businessName||'Baitan Thai Massage'}</strong><br>${siteConfig.address||''}<br><a href="tel:${siteConfig.phoneHref||''}">${siteConfig.phoneDisplay||''}</a><br><a href="mailto:${siteConfig.email||''}">${siteConfig.email||''}</a></p><p>KVK: ${siteConfig.kvk||''}<br>BTW: ${siteConfig.btw||''}</p>`,
      href:'/contact'
    }
  };
  document.querySelectorAll('[data-legal-modal]').forEach(btn=>btn.addEventListener('click',()=>{
    const item=legalContent[btn.dataset.legalModal];
    if(!item)return;
    title.textContent=item.title;
    body.innerHTML=item.html;
    link.href=item.href;
    if(typeof legalDialog.showModal==='function')legalDialog.showModal();
    else legalDialog.setAttribute('open','');
  }));
}

// Shared dialog controls and backdrop close.
document.querySelectorAll('[data-dialog-close]').forEach(btn=>btn.addEventListener('click',()=>{
  const dialog=btn.closest('dialog');
  if(dialog?.close)dialog.close(); else dialog?.removeAttribute('open');
}));
document.querySelectorAll('dialog.site-dialog').forEach(dialog=>{
  dialog.addEventListener('click',e=>{
    if(e.target===dialog){
      const rect=dialog.getBoundingClientRect();
      const inside=e.clientX>=rect.left&&e.clientX<=rect.right&&e.clientY>=rect.top&&e.clientY<=rect.bottom;
      if(!inside){if(dialog.close)dialog.close();else dialog.removeAttribute('open');}
    }
  });
});


/* Image fallback: never leave a broken image visible. */
document.addEventListener('error', function (event) {
  const img = event.target;
  if (!(img instanceof HTMLImageElement) || img.dataset.fallbackApplied === 'true') return;
  const fallback = window.BAITAN_SITE && window.BAITAN_SITE.hero && window.BAITAN_SITE.hero.image;
  if (!fallback || img.src === fallback) return;
  img.dataset.fallbackApplied = 'true';
  img.src = fallback;
}, true);
