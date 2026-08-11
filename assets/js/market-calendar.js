(()=>{
  const dayNames=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

  function validText(value){
    return typeof value==='string'&&Boolean(value.trim());
  }

  function parseDate(value){
    if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return null;
    const date=new Date(`${value}T12:00:00+08:00`);
    return Number.isFinite(date.getTime())&&date.toISOString().slice(0,10)===value?date:null;
  }

  function dateLabel(date,index){
    return `${dayNames[index]} (${date.getUTCMonth()+1}/${date.getUTCDate()})`;
  }

  function validMarketCalendarData(data){
    if(!data||typeof data!=='object'||Array.isArray(data))return false;
    if(!validText(data.updated_at)||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+08:00$/.test(data.updated_at)||!Number.isFinite(Date.parse(data.updated_at)))return false;
    if(!parseDate(data.week_start)||!parseDate(data.week_end))return false;
    if(!Array.isArray(data.days)||data.days.length!==7)return false;

    const start=parseDate(data.week_start);
    const end=parseDate(data.week_end);
    if(start.getUTCDay()!==1||end.getUTCDay()!==0||end.getTime()-start.getTime()!==6*86400000)return false;

    return data.days.every((day,index)=>{
      if(!day||typeof day!=='object'||Array.isArray(day))return false;
      if(!validText(day.label)||!validText(day.event))return false;
      const date=parseDate(day.date);
      if(!date||date.getTime()-start.getTime()!==index*86400000)return false;
      return day.label.trim()===dateLabel(date,index);
    });
  }

  function renderMarketCalendar(list,days){
    const fragment=document.createDocumentFragment();

    days.forEach(day=>{
      const item=document.createElement('li');
      const label=document.createElement('span');
      const date=document.createElement('span');
      const separator=document.createElement('span');
      const event=document.createElement('span');

      label.className='market-calendar-label';
      date.className='market-calendar-date';
      date.textContent=day.label.trim();
      separator.textContent=':';
      event.className='market-calendar-event';
      event.textContent=day.event.trim();

      label.append(date,separator);
      item.append(label,event);
      fragment.append(item);
    });

    list.replaceChildren(fragment);
  }

  async function loadMarketCalendar(){
    const list=document.querySelector('[data-market-calendar]');
    if(!list)return;

    try{
      const root=document.body.dataset.root||'.';
      const response=await fetch(`${root}/data/market-calendar.json`,{
        cache:'no-store',headers:{accept:'application/json'}
      });
      if(!response.ok)throw new Error(`Market Calendar HTTP ${response.status}`);

      const data=await response.json();
      if(!validMarketCalendarData(data))throw new Error('Market Calendar data format is invalid');
      renderMarketCalendar(list,data.days);
      list.dataset.marketCalendarStatus='loaded';
    }catch(error){
      console.error('Market Calendar update failed',error);
    }
  }

  document.addEventListener('DOMContentLoaded',loadMarketCalendar,{once:true});
})();
