"""XML 파서/정규화 단위 테스트."""
from scienceon_mcp.parser import normalize, parse_response

ARTI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<MetaData>
  <resultSummary><TotalCount>2</TotalCount><statusCode>200</statusCode></resultSummary>
  <parameterData><item metaCode="ParameterValue" ParameterName="searchQuery">{"BI":"x"}</item></parameterData>
  <recordList>
    <record>
      <item metaCode="CN">JAKO123</item>
      <item metaCode="Title">테스트 제목</item>
      <item metaCode="Author">홍길동</item>
      <item metaCode="Pubyear">2024</item>
      <item metaCode="Abstract">초록 내용</item>
      <item metaCode="Keyword">키워드1 . 키워드2</item>
      <item metaCode="ContentURL">http://example/x</item>
      <item metaCode="Lang">한국어</item>
    </record>
    <record><item metaCode="CN">JAKO456</item><item metaCode="Title">제목2</item></record>
  </recordList>
</MetaData>"""

ZERO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<MetaData>
  <resultSummary><TotalCount>0</TotalCount><statusCode>200</statusCode></resultSummary>
  <parameterData><item metaCode="ParameterValue">{"BI":"none"}</item></parameterData>
  <recordList></recordList>
</MetaData>"""


def test_parse_response_records():
    total, raws = parse_response(ARTI_XML)
    assert total == 2
    assert len(raws) == 2  # parameterData 의 item 은 레코드로 세지 않음
    r = normalize(raws[0], "ARTI")
    assert r.control_no == "JAKO123"
    assert r.title == "테스트 제목"
    assert r.authors == ["홍길동"]
    assert r.pub_year == "2024"
    assert r.url == "http://example/x"
    assert r.raw.get("Lang") == "한국어"


def test_parse_zero_results_no_phantom_record():
    total, raws = parse_response(ZERO_XML)
    assert total == 0
    assert raws == []  # 0건 응답에서 가짜 빈 레코드가 생기지 않아야 함
