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
if(mobileBook&&bookingSection&&'IntersectionObserver' in window){
  const mobileBookObserver=new IntersectionObserver(entries=>{
    const entry=entries[0];
    mobileBook.classList.toggle('is-hidden',entry.isIntersecting&&entry.intersectionRatio>.08);
  },{threshold:[0,.08,.2]});
  mobileBookObserver.observe(bookingSection);
}
