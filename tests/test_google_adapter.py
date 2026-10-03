import httpx
from backend.ai import Models
from backend.config import Settings


def test_google_request_omits_unsupported_seed(monkeypatch):
    bodies=[]
    def post(url,**kwargs):
        bodies.append(kwargs['json'])
        return httpx.Response(200,json={'choices':[{'message':{'content':'OK'}}]},request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx,'post',post)
    settings=Settings(cloud_model_url='https://generativelanguage.googleapis.com/v1beta/openai',cloud_api_key='test',cloud_model='test-model',cloud_fallback_to_local=False)
    models=Models(settings)
    assert models.complete([{'role':'user','content':'Hello'}])==('OK','cloud')
    assert 'seed' not in bodies[0]
    models.complete([{'role':'user','content':'Hello'}],force_local=True)
    assert bodies[1]['seed']==42


def test_google_transient_failure_retries_without_local_fallback(monkeypatch):
    calls=[]
    def post(url,**kwargs):
        calls.append(url)
        if len(calls)==1:
            return httpx.Response(503,request=httpx.Request('POST',url))
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"candidate":null,"related_id":null}'}}]},request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx,'post',post)
    monkeypatch.setattr('backend.ai.time.sleep',lambda seconds:None)
    models=Models(Settings(cloud_model_url='https://generativelanguage.googleapis.com/v1beta/openai',cloud_api_key='test',cloud_fallback_to_local=False))
    value,route=models.candidate('I prefer short explanations.',[])
    assert value['candidate'] is None and route=='cloud'
    assert len(calls)==2 and all('googleapis.com' in url for url in calls)


def test_greetings_and_identity_questions_need_no_extraction_call(monkeypatch):
    models=Models(Settings())
    def unexpected(*args,**kwargs):
        raise AssertionError('No AI request should be made')
    monkeypatch.setattr(models,'complete',unexpected)
    for text in ['Hello!', 'hello which model is this', 'What model are you?']:
        assert models.candidate(text,[])[0]['candidate'] is None


def test_greeting_with_personal_fact_is_still_extracted(monkeypatch):
    models=Models(Settings())
    calls=[]
    def complete(*args,**kwargs):
        calls.append(args)
        return '{"candidate":null,"related_id":null}','cloud'
    monkeypatch.setattr(models,'complete',complete)
    models.candidate('Hello, I prefer short explanations.',[])
    assert len(calls)==1


def test_google_quota_errors_are_not_retried(monkeypatch):
    calls=[]
    def post(url,**kwargs):
        calls.append(url)
        return httpx.Response(429,request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx,'post',post)
    models=Models(Settings(cloud_model_url='https://generativelanguage.googleapis.com/v1beta/openai',cloud_api_key='test',cloud_fallback_to_local=False))
    import pytest
    with pytest.raises(RuntimeError,match='quota or rate limit'):
        models.complete([{'role':'user','content':'Test'}])
    assert len(calls)==1
