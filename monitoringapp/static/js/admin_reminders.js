
        (() => {
            'use strict';
            const items = JSON.parse(document.getElementById('reminderData').textContent);
            let month = document.getElementById('adminReminderMonth').textContent.trim(); const today = document.getElementById('adminReminderToday').textContent.trim();
            const list = document.getElementById('reminderList');
            const editDialog = document.getElementById('editDialog'), deleteDialog = document.getElementById('deleteDialog');
            const form = document.getElementById('reminderForm');
            const title = document.getElementById('reminderTitle'), description = document.getElementById('reminderDescription');
            const eventAt = document.getElementById('eventAt'), remindAt = document.getElementById('remindAt'), preset = document.getElementById('reminderPreset');
            const requestedDate = new URLSearchParams(window.location.search).get('date');
            const validRequestedDate = requestedDate && /^\d{4}-\d{2}-\d{2}$/.test(requestedDate) && requestedDate.startsWith(month + '-') && !isNaN(new Date(requestedDate + 'T12:00:00'));
            let selected = validRequestedDate ? requestedDate : (today.startsWith(month) ? today : month + '-01'), status = 'all', scope = 'day';
            const pad = n => String(n).padStart(2, '0');
            const dateValue = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
            const dateLabel = d => new Date(d + 'T12:00:00').toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
            const timeLabel = d => new Date(d).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit', hour12: true });
            function icons() { if (window.lucide) lucide.createIcons(); }
            function node(tag, cls, text) { const el = document.createElement(tag); el.className = cls; if (text !== undefined) el.textContent = text; return el; }
            function actionForm(item, action, label) {
                const f = node('form', ''); f.method = 'post'; f.setAttribute('action', form.getAttribute('action'));
                [['csrfmiddlewaretoken', form.elements.csrfmiddlewaretoken.value], ['action', action], ['reminder_id', item.id]].forEach(([name, value]) => { const input = document.createElement('input'); input.type = 'hidden'; input.name = name; input.value = value; f.append(input); });
                const b = node('button', 'reminder-btn', label); b.type = 'submit'; f.append(b);
                f.addEventListener('submit', async event => {
                    event.preventDefault(); b.disabled = true; const feedback = document.getElementById('reminderFeedback'); feedback.hidden = true;
                    try {
                        const response = await fetch(f.getAttribute('action'), { method: 'POST', body: new FormData(f), credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' } });
                        if (!response.ok || !(response.headers.get('content-type') || '').includes('application/json')) throw new Error('Could not update status. Check your session and the Complete/Reopen view change.');
                        const result = await response.json(); if (!result.ok || Number(result.id) !== Number(item.id)) throw new Error('Reminder update was not confirmed.');
                        item.is_completed = result.is_completed; feedback.hidden = true; window.showToast(result.message || (item.is_completed ? 'Reminder completed.' : 'Reminder reopened.'), 'success'); render();
                    } catch (error) { feedback.hidden = true; window.showToast(error.message || 'Unable to update. Please try again.', 'error'); b.disabled = false; }
                }); return f;
            }
            function openDialog(dialog) {
                dialog.showModal();
                // Keep reusable toasts visible above a native dialog's backdrop.
                const container = document.getElementById('toastContainer');
                if (container) dialog.appendChild(container);
                document.body.classList.add('modal-open');
            }
            [editDialog, deleteDialog].forEach(dialog => { dialog.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', () => dialog.close())); dialog.addEventListener('close', () => {
                    const container = document.getElementById('toastContainer');
                    if (container) document.body.appendChild(container);
                    document.body.classList.remove('modal-open');
                }); });
            const controls = Array.from(document.querySelectorAll('.datetime-control'));
            function closePickers() { controls.forEach(c => { c.querySelector('.picker-panel').hidden = true; c.querySelector('.picker-panel').replaceChildren(); c.querySelectorAll('.picker-trigger').forEach(b => b.setAttribute('aria-expanded', 'false')); }); }
            function syncDateControls() { controls.forEach(c => { const value = document.getElementById(c.dataset.input).value; const d = value ? new Date(value) : null; c.querySelector('.date-trigger span').textContent = d && !isNaN(d) ? d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Select date'; c.querySelector('.time-trigger span').textContent = d && !isNaN(d) ? d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) : 'Select time'; }); }
            function setControl(c, date, time) { const input = document.getElementById(c.dataset.input); input.value = date + 'T' + time; input.dispatchEvent(new Event('input', { bubbles: true })); syncDateControls(); document.getElementById('pickerError').hidden = true; closePickers(); }
            function pickerButton(label, cls, click) { const b = node('button', cls, label); b.type = 'button'; b.addEventListener('click', click); return b; }
            controls.forEach(c => {
                const panel = c.querySelector('.picker-panel'), input = document.getElementById(c.dataset.input);
                const dateButton = c.querySelector('.date-trigger'), timeButton = c.querySelector('.time-trigger');
                function show(trigger) { const wasOpen = trigger.getAttribute('aria-expanded') === 'true'; closePickers(); if (wasOpen) return false; panel.hidden = false; trigger.setAttribute('aria-expanded', 'true'); return true; }
                dateButton.addEventListener('click', () => {
                    if (!show(dateButton)) return;
                    let base = input.value ? new Date(input.value) : new Date(selected + 'T09:00'); let year = base.getFullYear(), mon = base.getMonth();
                    function draw() {
                        panel.replaceChildren(); const top = node('div', 'picker-top'); top.append(pickerButton('‹', 'picker-nav', () => { mon--; if (mon < 0) { mon = 11; year--; } draw(); }), node('strong', '', new Date(year, mon, 1).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })), pickerButton('›', 'picker-nav', () => { mon++; if (mon > 11) { mon = 0; year++; } draw(); })); panel.append(top);
                        const grid = node('div', 'picker-calendar');['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'].forEach(x => grid.append(node('span', 'picker-weekday', x)));
                        const start = new Date(year, mon, 1).getDay(), days = new Date(year, mon + 1, 0).getDate(); for (let i = 0; i < start; i++)grid.append(node('span', ''));
                        for (let day = 1; day <= days; day++) { const value = year + '-' + pad(mon + 1) + '-' + pad(day); const b = pickerButton(String(day), 'picker-date' + (input.value.startsWith(value) ? ' chosen' : '') + (value === today ? ' current' : ''), () => { setControl(c, value, input.value.split('T')[1] || '09:00'); dateButton.focus(); }); b.setAttribute('aria-label', dateLabel(value)); grid.append(b); } panel.append(grid);
                        const footer = node('div', 'picker-footer'); footer.append(pickerButton('Cancel', '', () => { closePickers(); dateButton.focus(); }), pickerButton('Today', '', () => { setControl(c, today, input.value.split('T')[1] || '09:00'); dateButton.focus(); })); panel.append(footer);
                    } draw();
                });
                timeButton.addEventListener('click', () => {
                    if (!show(timeButton)) return; panel.replaceChildren(); panel.append(node('strong', '', 'Select time'));
                    const oldTime = input.value.split('T')[1] || '09:00'; let [hour, minute] = oldTime.split(':').map(Number), period = hour >= 12 ? 'PM' : 'AM';
                    const editor = node('div', 'time-editor'), hh = document.createElement('input'), mm = document.createElement('input'); hh.type = mm.type = 'number'; hh.min = '1'; hh.max = '12'; mm.min = '0'; mm.max = '59'; hh.step = mm.step = '1'; hh.value = pad(hour % 12 || 12); mm.value = pad(minute); hh.setAttribute('aria-label', 'Hour'); mm.setAttribute('aria-label', 'Minute'); const periods = node('div', 'time-period');['AM', 'PM'].forEach(p => { const b = pickerButton(p, '', () => { period = p; periods.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x.textContent === period))); }); b.setAttribute('aria-pressed', String(p === period)); periods.append(b); }); editor.append(hh, node('span', '', ':'), mm, periods); panel.append(editor);
                    const error = node('p', 'picker-error', 'Enter hour 1–12 and minute 0–59.'); error.hidden = true; panel.append(error);
                    const footer = node('div', 'picker-footer'); footer.append(pickerButton('Cancel', '', () => { closePickers(); timeButton.focus(); }), pickerButton('Set time', 'set-time', () => { const h = Number(hh.value), m = Number(mm.value); if (!hh.value || !mm.value || !Number.isInteger(h) || !Number.isInteger(m) || h < 1 || h > 12 || m < 0 || m > 59) { error.hidden = false; return; } const h24 = h % 12 + (period === 'PM' ? 12 : 0); setControl(c, input.value.split('T')[0] || selected, pad(h24) + ':' + pad(m)); timeButton.focus(); })); panel.append(footer);
                });
            });
            editDialog.addEventListener('click', event => { if (!event.target.closest('.datetime-control')) closePickers(); });
            editDialog.addEventListener('cancel', event => { if (controls.some(c => !c.querySelector('.picker-panel').hidden)) { event.preventDefault(); closePickers(); } });
            editDialog.addEventListener('close', closePickers);
            function updatePreset() { if (preset.value === 'custom' || !eventAt.value) return; const d = new Date(eventAt.value); d.setMinutes(d.getMinutes() - Number(preset.value)); remindAt.value = dateValue(d); remindAt.setCustomValidity(''); syncDateControls(); }
            function edit(item) { form.reset(); document.getElementById('formAction').value = item ? 'update' : 'create'; document.getElementById('reminderId').value = item ? item.id : ''; document.getElementById('editHeading').textContent = item ? 'Edit reminder' : 'Add reminder'; title.value = item ? item.title : ''; description.value = item ? item.description : ''; eventAt.value = item ? item.event_at : selected + 'T09:00'; preset.value = item ? 'custom' : '1440'; remindAt.value = item ? item.remind_at : ''; if (!item) updatePreset(); remindAt.setCustomValidity(''); closePickers(); syncDateControls(); document.getElementById('pickerError').hidden = true; openDialog(editDialog); }
            function render() {
                document.getElementById('selectedDateLabel').textContent = dateLabel(selected);
                document.querySelectorAll('.day[data-day]').forEach(button => { const date = month + '-' + pad(button.dataset.day); button.classList.toggle('selected', date === selected); button.classList.toggle('today', date === today); button.setAttribute('aria-pressed', String(date === selected)); const matches = items.filter(i => i.date === date); button.setAttribute('aria-label', dateLabel(date) + `, ${matches.length} reminder${matches.length === 1 ? '' : 's'}`); const old = button.querySelector('.dot'); if (old) old.remove(); if (matches.length) { const dot = node('span', 'dot' + (matches.every(i => i.is_completed) ? ' completed' : '')); dot.setAttribute('aria-hidden', 'true'); button.append(dot); } });
                list.replaceChildren();
                document.getElementById('totalCount').textContent = items.length;
                document.getElementById('completedCount').textContent = items.filter(i => i.is_completed).length;
                document.getElementById('activeCount').textContent = items.filter(i => !i.is_completed).length;
                document.getElementById('overdueCount').textContent = items.filter(i => !i.is_completed && new Date(i.event_at) < new Date()).length;
                document.getElementById('selectedHeading').textContent = scope === 'month' ? 'This month’s reminders' : 'Selected date';
                document.getElementById('selectedDateLabel').textContent = scope === 'month' ? '{{ month_label }}' : dateLabel(selected);
                const query = document.getElementById('reminderSearch').value.trim().toLocaleLowerCase();
                const filtered = items.filter(i => (scope === 'month' || i.date === selected) && (status === 'all' || (status === 'completed' ? i.is_completed : !i.is_completed)) && (!query || (i.title + ' ' + i.description).toLocaleLowerCase().includes(query)));
                if (!filtered.length) { list.append(node('div', 'empty', 'No matching reminders. Try another date or filter.')); }
                filtered.forEach(item => { const overdue = !item.is_completed && new Date(item.event_at) < new Date(); const card = node('article', 'reminder-card' + (item.is_completed ? ' is-completed' : '') + (overdue ? ' is-overdue' : '')); card.append(node('h3', '', item.title)); if (item.is_completed) card.append(node('span', 'completed-label', 'Completed')); else if (overdue) card.append(node('span', 'overdue-label', 'Event overdue')); if (item.description) card.append(node('p', '', item.description)); card.append(node('span', 'reminder-meta', 'Event: ' + timeLabel(item.event_at))); card.append(node('span', 'reminder-meta', 'Reminder: ' + timeLabel(item.remind_at))); const actions = node('div', 'reminder-card-actions'); const editButton = node('button', 'reminder-btn', 'Edit'); editButton.type = 'button'; editButton.addEventListener('click', () => edit(item)); const deleteButton = node('button', 'reminder-btn danger', 'Delete'); deleteButton.type = 'button'; deleteButton.addEventListener('click', () => { document.getElementById('deleteId').value = item.id; document.getElementById('deleteDescription').textContent = item.title; openDialog(deleteDialog); }); actions.append(editButton, actionForm(item, item.is_completed ? 'reopen' : 'complete', item.is_completed ? 'Reopen' : 'Complete'), deleteButton); card.append(actions); list.append(card); });
            }
            document.querySelector('.calendar-grid').addEventListener('click', event => { const b=event.target.closest('.day[data-day]'); if(!b)return; selected = month + '-' + pad(b.dataset.day); scope = 'day'; document.querySelectorAll('[data-scope]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.scope === scope))); render(); });
            document.querySelectorAll('[data-status]').forEach(b => b.addEventListener('click', () => { status = b.dataset.status; document.querySelectorAll('[data-status]').forEach(x => x.setAttribute('aria-pressed', String(x === b))); render(); }));
            let loading = false;
            function navigationLinks() {
                const [year, monthNumber] = month.split('-').map(Number);
                [-1,1].forEach(offset => { const d=new Date(year,monthNumber-1+offset,1); document.getElementById(offset<0?'previousMonth':'nextMonth').href='?month='+d.getFullYear()+'-'+pad(d.getMonth()+1); });
            }
            async function loadMonth(value, navigate=false) {
                if(loading || (!navigate && (document.hidden || editDialog.open || deleteDialog.open)))return;
                loading=true;
                try {
                    const url=new URL(form.getAttribute('action'),location.origin); url.searchParams.set('month',value); url.searchParams.set('format','json');
                    const response=await fetch(url,{credentials:'same-origin',headers:{'X-Requested-With':'XMLHttpRequest'},signal:AbortSignal.timeout(15000)});
                    const data=await response.json(); if(!response.ok || !data.ok)throw new Error(data.message || 'Unable to load reminders.');
                    const changedMonth=month!==data.selected_month;
                    const changedItems=JSON.stringify(items)!==JSON.stringify(data.items);
                    month=data.selected_month;
                    items.splice(0,items.length,...data.items);
                    if(changedMonth){
                        selected=today.startsWith(month)?today:month+'-01';
                        const grid=document.querySelector('.calendar-grid'); grid.querySelectorAll('.day').forEach(el=>el.remove());
                        data.calendar_weeks.flat().forEach(day=>{const el=node(day?'button':'span','day'+(day?'':' blank'),day?String(day):'');if(day){el.type='button';el.dataset.day=day;}else el.setAttribute('aria-hidden','true');grid.append(el);});
                    }
                    document.getElementById('monthHeading').textContent=data.month_label; document.querySelector('.overview-month').textContent=data.month_label;
                    navigationLinks(); if(changedMonth || changedItems || navigate)render();
                    if(navigate){const browserUrl=new URL(location.href);browserUrl.searchParams.set('month',month);browserUrl.searchParams.delete('date');history.replaceState(null,'',browserUrl);}
                } catch(error){if(navigate)window.showToast(error.message,'error');}
                finally{loading=false;}
            }
            navigationLinks();
            document.querySelector('.calendar-controls').addEventListener('click',event=>{const a=event.target.closest('a');if(!a)return;event.preventDefault();const value=a.id==='previousMonth'||a.id==='nextMonth'?new URL(a.href).searchParams.get('month'):today.slice(0,7);loadMonth(value,true);});
            async function saveForm(target, dialog) {
                const button=target.querySelector('button[type="submit"]');if(button.disabled)return;button.disabled=true;
                try {
                    const response=await fetch(target.getAttribute('action'),{method:'POST',credentials:'same-origin',body:new FormData(target),headers:{'X-Requested-With':'XMLHttpRequest'},signal:AbortSignal.timeout(15000)});
                    const result=await response.json(); if(!response.ok || !result.ok)throw new Error(result.message || 'Unable to save reminder.');
                    if(result.item){const i=items.findIndex(x=>x.id===result.item.id);if(result.item.date.startsWith(month)){if(i<0)items.push(result.item);else items[i]=result.item;}else if(i>=0)items.splice(i,1);}
                    else {const i=items.findIndex(x=>x.id===result.id);if(i>=0)items.splice(i,1);}
                    items.sort((a,b)=>a.event_at.localeCompare(b.event_at)||a.id-b.id);dialog.close();render();window.showToast(result.message,'success');
                } catch(error){window.showToast(error.message,'error');}
                finally{button.disabled=false;}
            }
            deleteDialog.querySelector('form').addEventListener('submit',event=>{event.preventDefault();saveForm(event.currentTarget,deleteDialog);});
            const liveTimer=setInterval(()=>loadMonth(month),10000);
            document.addEventListener('visibilitychange',()=>{if(!document.hidden)loadMonth(month);});
            window.addEventListener('pagehide',()=>clearInterval(liveTimer),{once:true});
            document.getElementById('newReminder').addEventListener('click', () => edit(null)); document.getElementById('addSelected').addEventListener('click', () => edit(null)); preset.addEventListener('change', updatePreset); eventAt.addEventListener('input', () => { remindAt.setCustomValidity(''); updatePreset(); }); remindAt.addEventListener('input', () => { preset.value = 'custom'; remindAt.setCustomValidity(''); });
            form.addEventListener('submit', event => {
                event.preventDefault();
                const remind = new Date(remindAt.value), start = new Date(eventAt.value); let error = '';
                if (!eventAt.value || !remindAt.value || isNaN(start) || isNaN(remind)) error = 'Select an event date/time and a reminder date/time.';
                else if (remind > start) error = 'Reminder must be on or before the event.';
                else if (remind <= new Date()) { const original=items.find(i=>String(i.id)===document.getElementById('reminderId').value); if(!original || original.event_at!==eventAt.value || original.remind_at!==remindAt.value)error='Choose a future reminder time.'; }
                const notice = document.getElementById('pickerError'); notice.textContent = error; notice.hidden = !error;
                if (error) { event.preventDefault(); window.showToast(error, 'warning'); notice.scrollIntoView({ block: 'nearest' }); }
                else saveForm(form,editDialog);
            });
            document.getElementById('reminderSearch').addEventListener('input', render);
            document.querySelectorAll('[data-scope]').forEach(b => b.addEventListener('click', () => { scope = b.dataset.scope; document.querySelectorAll('[data-scope]').forEach(x => x.setAttribute('aria-pressed', String(x === b))); render(); }));
            let validationToastPending = false;
            form.addEventListener('invalid', event => {
                if (validationToastPending) return;
                validationToastPending = true;
                window.showToast(event.target.validationMessage || 'Check the reminder fields.', 'warning');
                setTimeout(() => { validationToastPending = false; }, 0);
            }, true);
            render(); icons();
        })();
    