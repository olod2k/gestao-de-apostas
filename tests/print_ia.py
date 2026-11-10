import asyncio
from playwright.async_api import async_playwright
import os
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
APP = 'file://' + os.path.join(os.path.dirname(HERE), 'index.html')
XLSX_JS=open('node_modules/xlsx/dist/xlsx.full.min.js').read()
MOCK = r"""
window.__calls = [];
window.__mode = 'ok';
window.cloudBets = { configured:false, user:null,
  readSlip: async ({data, mimeType, prompt, model}) => {
    window.__calls.push({model, mimeType, len:data.length, prompt});
    await new Promise(r=>setTimeout(r,300));
    if(window.__mode==='403') throw new Error('Firebase AI: The Firebase AI Logic API is not enabled (api-not-enabled) 403');
    if(model==='gemini-3.8-flash') throw new Error('[404 ] models/gemini-3.8-flash is not found');
    return '```json\n' + JSON.stringify({apostas:[
      {data:'07/11', esporte:'Futebol', competicao:'Brasileirão', casa:'Bet365', time1:'Palmeiras', time2:'Santos', mercado:'Resultado Final: Palmeiras', multipla:false, stake:'25,50', odd:1.85, resultado:'pendente', retorno_cashout:null},
      {data:'', esporte:'Futebol', competicao:'', casa:'Betano', time1:'Múltipla', time2:'', mercado:'Palmeiras vence (Palmeiras x Santos) + Over 2.5 (Fla x Grêmio)', multipla:true, stake:10, odd:3.4, resultado:'cashout', retorno_cashout:18.2}
    ]}) + '\n```';
  }
};
"""
errs=[]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        ctx=await b.new_context(viewport={'width':390,'height':844})
        async def route(r):
            u=r.request.url
            if 'cdnjs' in u: await r.fulfill(body=XLSX_JS,content_type='application/javascript')
            elif u.startswith('file://'): await r.continue_()
            else: await r.abort()
        await ctx.route('**/*',route)
        await ctx.add_init_script(MOCK)
        pg=await ctx.new_page()
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(APP+'#nova'); await pg.wait_for_timeout(500)
        await pg.set_input_files('#slip-file','print_exemplo.png')
        await pg.wait_for_timeout(150); print('busy:', await pg.text_content('#slip-title'))
        await pg.wait_for_timeout(1200)
        print('status:', await pg.text_content('#slip-status'))
        print('calls:', await pg.evaluate("__calls.map(c=>c.model+' '+c.mimeType+' '+c.len)"))
        f = await pg.evaluate("['f-data','f-sport','f-comp','f-bookie','f-team1','f-team2','f-market','f-odd','f-stake','f-cashout'].map(i=>i+'='+document.getElementById(i).value)")
        print(f, await pg.text_content('#preview-value'), await pg.evaluate("document.querySelector('#result-chips .active').textContent"), await pg.evaluate("document.querySelector('#kind-toggle .active').textContent"))
        await pg.screenshot(path='m_slip.png')
        await pg.click('#submit-btn'); await pg.wait_for_timeout(400)
        print('after submit status:', await pg.text_content('#slip-status'))
        f = await pg.evaluate("['f-team1','f-market','f-odd','f-stake','f-cashout'].map(i=>i+'='+document.getElementById(i).value)")
        print(f, await pg.evaluate("document.querySelector('#result-chips .active').textContent"), await pg.evaluate("document.querySelector('#kind-toggle .active').textContent"), await pg.text_content('#preview-value'))
        await pg.click('#submit-btn'); await pg.wait_for_timeout(400)
        print('after 2nd:', repr(await pg.text_content('#slip-status')))
        bets = await pg.evaluate("JSON.parse(localStorage.getItem('bets')).map(b=>[b.date,b.team1,b.stake,b.odd,b.result,b.profit,b.kind,b.cashout])")
        print(bets)
        print('model ok stored:', await pg.evaluate("localStorage.getItem('apostas_ai_model_ok')"))
        print('prompt has casas:', 'Bet365' in (await pg.evaluate("__calls[__calls.length-1].prompt")))
        await pg.evaluate("__mode='403'")
        await pg.set_input_files('#slip-file','print_exemplo.png'); await pg.wait_for_timeout(900)
        print('403:', await pg.text_content('#slip-status'))
        await pg.goto(APP+'#banca'); await pg.wait_for_timeout(400)
        print('ai model field:', await pg.input_value('#ai-model'), '|', await pg.text_content('#ai-status'))
        await b.close()
    print('ERRS',errs)
asyncio.run(main())
