# GraphRAG OpenRouter Benchmark Evaluation Report

- **Evaluated Samples**: 20
- **LLM Model**: `google/gemma-4-26b-a4b-it:free`
- **Knowledge Base**: `iso19650_kg_unified.ttl` (17,931 Triples / 618 Nodes)

## Summary Metrics Table

| ID | Question | Citation | Retrieval Status | RAG Answer Status |
| :--- | :--- | :--- | :--- | :--- |
| **RAGAS-ISO-001** | Khái niệm 'asset life' được định nghĩa như thế nào trong tiê... | `ISO 55000:2024 Clause 3.1.2` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-002** | Khái niệm 'life cycle management' được định nghĩa như thế nà... | `ISO 55000:2024 Clause 3.1.4` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-003** | Khái niệm 'asset type' được định nghĩa như thế nào trong tiê... | `ISO 55000:2024 Clause 3.1.5` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-004** | Khái niệm 'asset system' được định nghĩa như thế nào trong t... | `ISO 55000:2024 Clause 3.1.6` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-005** | Khái niệm 'asset portfolio' được định nghĩa như thế nào tron... | `ISO 55000:2024 Clause 3.1.7` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-006** | Khái niệm 'critical asset' được định nghĩa như thế nào trong... | `ISO 55000:2024 Clause 3.1.8` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-007** | Khái niệm 'object' được định nghĩa như thế nào trong tiêu ch... | `ISO 55000:2024 Clause 3.1.9` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-008** | Khái niệm 'data' được định nghĩa như thế nào trong tiêu chuẩ... | `ISO 55000:2024 Clause 3.1.10` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-009** | Khái niệm 'organizational objective' được định nghĩa như thế... | `ISO 55000:2024 Clause 3.2.2` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-010** | Khái niệm 'organizational plan' được định nghĩa như thế nào ... | `ISO 55000:2024 Clause 3.2.3` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-011** | Khái niệm 'management' được định nghĩa như thế nào trong tiê... | `ISO 55000:2024 Clause 3.2.4` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-012** | Khái niệm 'level of service' được định nghĩa như thế nào tro... | `ISO 55000:2024 Clause 3.2.7` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-013** | Khái niệm 'organization' được định nghĩa như thế nào trong t... | `ISO 55000:2024 Clause 3.3.1` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-014** | Khái niệm 'stakeholder' được định nghĩa như thế nào trong ti... | `ISO 55000:2024 Clause 3.3.2` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-015** | Khái niệm 'management system' được định nghĩa như thế nào tr... | `ISO 55000:2024 Clause 3.3.4` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-016** | Khái niệm 'asset management system' được định nghĩa như thế ... | `ISO 55000:2024 Clause 3.3.5` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-017** | Khái niệm 'policy' được định nghĩa như thế nào trong tiêu ch... | `ISO 55000:2024 Clause 3.3.6` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-018** | Khái niệm 'objective' được định nghĩa như thế nào trong tiêu... | `ISO 55000:2024 Clause 3.3.7` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-019** | Khái niệm 'risk' được định nghĩa như thế nào trong tiêu chuẩ... | `ISO 55000:2024 Clause 3.3.8` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |
| **RAGAS-ISO-020** | Khái niệm 'opportunity' được định nghĩa như thế nào trong ti... | `ISO 55000:2024 Clause 3.3.9` | `PASS` (100% RDF Triple Match) | `PASS` (100% Faithful) |

## Detailed Side-by-Side Benchmark Results

### Sample #1: RAGAS-ISO-001
- **Question**: Khái niệm 'asset life' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.2?
- **Ground Truth**: Khái niệm 'asset life' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.2 được định nghĩa là: period from asset ideation to asset end of life
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.2`

```turtle
# Retrieved RDF Subgraph Context
iso:term_asset_life a iso:Concept ;
  rdfs:label "asset life" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.2" ;
  iso:definition "period from asset ideation to asset end of life" ;
  iso:pdmRelevance "high" .
```

#### RAG Generated Answer:
Theo Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'asset life'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.1.2** như sau:

"asset life" là khoảng thời gian tính từ khi hình thành ý tưởng về tài sản (asset ideation) cho đến khi kết thúc vòng đời của tài sản đó (asset end of life).

---

### Sample #2: RAGAS-ISO-002
- **Question**: Khái niệm 'life cycle management' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.4?
- **Ground Truth**: Khái niệm 'life cycle management' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.4 được định nghĩa là: applying asset management over the life cycle of assets
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.4`

```turtle
# Retrieved RDF Subgraph Context
iso:term_life_cycle_management a iso:Concept ;
  rdfs:label "life cycle management" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.4" ;
  iso:definition "applying asset management over the life cycle of assets" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'life cycle management'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.1.4** như sau:

"Applying asset management over the life cycle of assets" (Áp dụng quản lý tài sản trong suốt vòng đời của tài sản).

---

### Sample #3: RAGAS-ISO-003
- **Question**: Khái niệm 'asset type' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.5?
- **Ground Truth**: Khái niệm 'asset type' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.5 được định nghĩa là: grouping of assets having common characteristics that distinguish those assets as a group or class
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.5`

```turtle
# Retrieved RDF Subgraph Context
iso:term_asset_type a iso:Concept ;
  rdfs:label "asset type" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.5" ;
  iso:definition "grouping of assets having common characteristics that distinguish those assets as a group or class" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Theo tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.1.5**, khái niệm **'asset type'** (loại tài sản) được định nghĩa là:

"grouping of assets having common characteristics that distinguish those assets as a group or class" (nhóm các tài sản có các đặc điểm chung giúp phân biệt các tài sản đó như một nhóm hoặc một lớp).

---

### Sample #4: RAGAS-ISO-004
- **Question**: Khái niệm 'asset system' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.6?
- **Ground Truth**: Khái niệm 'asset system' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.6 được định nghĩa là: set of assets that interact or are interrelated
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.6`

```turtle
# Retrieved RDF Subgraph Context
iso:term_asset_system a iso:Concept ;
  rdfs:label "asset system" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.6" ;
  iso:definition "set of assets that interact or are interrelated" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'asset system'** được định nghĩa như sau:

Theo tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.1.6**, **'asset system'** là "một tập hợp các tài sản có sự tương tác hoặc có mối quan hệ lẫn nhau" (*set of assets that interact or are interrelated*).

---

### Sample #5: RAGAS-ISO-005
- **Question**: Khái niệm 'asset portfolio' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.7?
- **Ground Truth**: Khái niệm 'asset portfolio' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.7 được định nghĩa là: assets that are within the scope of an asset management system
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.7`

```turtle
# Retrieved RDF Subgraph Context
iso:term_asset_portfolio a iso:Concept ;
  rdfs:label "asset portfolio" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.7" ;
  iso:definition "assets that are within the scope of an asset management system" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Theo Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'asset portfolio'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.1.7** là:

"assets that are within the scope of an asset management system" (các tài sản nằm trong phạm vi của một hệ thống quản lý tài sản).

---

### Sample #6: RAGAS-ISO-006
- **Question**: Khái niệm 'critical asset' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.8?
- **Ground Truth**: Khái niệm 'critical asset' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.8 được định nghĩa là: asset having the potential to significantly impact the achievement of an organization's objectives
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.8`

```turtle
# Retrieved RDF Subgraph Context
iso:term_critical_asset a iso:Concept ;
  rdfs:label "critical asset" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.8" ;
  iso:definition "asset having the potential to significantly impact the achievement of an organization's objectives" ;
  iso:pdmRelevance "high" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'critical asset'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.1.8** như sau:

"Critical asset" là tài sản có tiềm năng gây ảnh hưởng đáng kể đến việc đạt được các mục tiêu của một tổ chức (*asset having the potential to significantly impact the achievement of an organization's objectives*).

---

### Sample #7: RAGAS-ISO-007
- **Question**: Khái niệm 'object' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.9?
- **Ground Truth**: Khái niệm 'object' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.9 được định nghĩa là: anything perceivable or conceivable
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.9`

```turtle
# Retrieved RDF Subgraph Context
iso:term_object a iso:Concept ;
  rdfs:label "object" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.9" ;
  iso:definition "anything perceivable or conceivable" ;
  iso:pdmRelevance "low" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'object'** được định nghĩa như sau:

Theo tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.1.9**, 'object' được định nghĩa là: *"anything perceivable or conceivable"* (bất cứ thứ gì có thể nhận thức được hoặc có thể hình dung được).

---

### Sample #8: RAGAS-ISO-008
- **Question**: Khái niệm 'data' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.1.10?
- **Ground Truth**: Khái niệm 'data' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.1.10 được định nghĩa là: facts about an object
- **Standard Citation**: `ISO 55000:2024 Clause 3.1.10`

```turtle
# Retrieved RDF Subgraph Context
iso:term_data a iso:Concept ;
  rdfs:label "data" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.1.10" ;
  iso:definition "facts about an object" ;
  iso:pdmRelevance "high" .
```

#### RAG Generated Answer:
Theo Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'data'** trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.1.10** được định nghĩa là:

**"facts about an object"** (các sự thật về một đối tượng).

---

### Sample #9: RAGAS-ISO-009
- **Question**: Khái niệm 'organizational objective' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.2.2?
- **Ground Truth**: Khái niệm 'organizational objective' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.2.2 được định nghĩa là: overarching objective that sets the context and direction for an organization's activities
- **Standard Citation**: `ISO 55000:2024 Clause 3.2.2`

```turtle
# Retrieved RDF Subgraph Context
iso:term_organizational_objective a iso:Concept ;
  rdfs:label "organizational objective" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.2.2" ;
  iso:definition "overarching objective that sets the context and direction for an organization's activities" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'organizational objective'** được định nghĩa như sau:

Theo tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.2.2**, **organizational objective** là: *"overarching objective that sets the context and direction for an organization's activities"* (mục tiêu bao quát nhằm thiết lập bối cảnh và định hướng cho các hoạt động của một tổ chức).

---

### Sample #10: RAGAS-ISO-010
- **Question**: Khái niệm 'organizational plan' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.2.3?
- **Ground Truth**: Khái niệm 'organizational plan' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.2.3 được định nghĩa là: documented information that specifies the plans to achieve the organizational objectives
- **Standard Citation**: `ISO 55000:2024 Clause 3.2.3`

```turtle
# Retrieved RDF Subgraph Context
iso:term_organizational_plan a iso:Concept ;
  rdfs:label "organizational plan" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.2.3" ;
  iso:definition "documented information that specifies the plans to achieve the organizational objectives" ;
  iso:pdmRelevance "low" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'organizational plan'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.2.3** như sau:

"Là thông tin được văn bản hóa nhằm chỉ định các kế hoạch để đạt được các mục tiêu của tổ chức" (*documented information that specifies the plans to achieve the organizational objectives*).

---

### Sample #11: RAGAS-ISO-011
- **Question**: Khái niệm 'management' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.2.4?
- **Ground Truth**: Khái niệm 'management' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.2.4 được định nghĩa là: coordinated activities to direct and control an organization
- **Standard Citation**: `ISO 55000:2024 Clause 3.2.4`

```turtle
# Retrieved RDF Subgraph Context
iso:term_management a iso:Concept ;
  rdfs:label "management" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.2.4" ;
  iso:definition "coordinated activities to direct and control an organization" ;
  iso:pdmRelevance "low" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'management'** được định nghĩa như sau:

Theo tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.2.4**, 'anagement' được định nghĩa là: *"coordinated activities to direct and control an organization"* (các hoạt động phối hợp để điều hành và kiểm soát một tổ chức).

---

### Sample #12: RAGAS-ISO-012
- **Question**: Khái niệm 'level of service' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.2.7?
- **Ground Truth**: Khái niệm 'level of service' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.2.7 được định nghĩa là: parameters, or combination of parameters, which reflect social, political, environmental and economic outcomes that an organization delivers
- **Standard Citation**: `ISO 55000:2024 Clause 3.2.7`

```turtle
# Retrieved RDF Subgraph Context
iso:term_level_of_service a iso:Concept ;
  rdfs:label "level of service" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.2.7" ;
  iso:definition "parameters, or combination of parameters, which reflect social, political, environmental and economic outcomes that an organization delivers" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'level of service'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.2.7** như sau:

"level of service" là các tham số, hoặc sự kết hợp của các tham số, phản ánh các kết quả về mặt xã hội, chính trị, môi trường và kinh tế mà một tổ chức mang lại (*parameters, or combination of parameters, which reflect social, political, environmental and economic outcomes that an organization delivers*).

---

### Sample #13: RAGAS-ISO-013
- **Question**: Khái niệm 'organization' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.1?
- **Ground Truth**: Khái niệm 'organization' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.1 được định nghĩa là: person or group of people that has its own functions with responsibilities, authorities and relationships to achieve its objectives
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.1`

```turtle
# Retrieved RDF Subgraph Context
iso:term_organization a iso:Concept ;
  rdfs:label "organization" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.1" ;
  iso:definition "person or group of people that has its own functions with responsibilities, authorities and relationships to achieve its objectives" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'organization'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.3.1** như sau:

"Là một cá nhân hoặc một nhóm người có các chức năng riêng biệt với các trách nhiệm, thẩm quyền và các mối quan hệ nhằm đạt được các mục tiêu của mình" (*person or group of people that has its own functions with responsibilities, authorities and relationships to achieve its objectives*).

---

### Sample #14: RAGAS-ISO-014
- **Question**: Khái niệm 'stakeholder' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.2?
- **Ground Truth**: Khái niệm 'stakeholder' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.2 được định nghĩa là: person or organization that can affect, be affected by, or perceive itself to be affected by a decision or activity
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.2`

```turtle
# Retrieved RDF Subgraph Context
iso:term_stakeholder a iso:Concept ;
  rdfs:label "stakeholder" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.2" ;
  iso:definition "person or organization that can affect, be affected by, or perceive itself to be affected by a decision or activity" ;
  iso:pdmRelevance "low" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'stakeholder'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.3.2** như sau:

"Là cá nhân hoặc tổ chức có thể ảnh hưởng, chịu ảnh hưởng bởi, hoặc tự nhận thấy mình bị ảnh hưởng bởi một quyết định hoặc hoạt động" (*person or organization that can affect, be affected by, or perceive itself to be affected by a decision or activity*).

---

### Sample #15: RAGAS-ISO-015
- **Question**: Khái niệm 'management system' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.4?
- **Ground Truth**: Khái niệm 'management system' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.4 được định nghĩa là: set of interrelated or interacting elements of an organization to establish policies and objectives, as well as processes to achieve those objectives
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.4`

```turtle
# Retrieved RDF Subgraph Context
iso:term_management_system a iso:Concept ;
  rdfs:label "management system" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.4" ;
  iso:definition "set of interrelated or interacting elements of an organization to establish policies and objectives, as well as processes to achieve those objectives" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'management system'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.3.4** như sau:

"Là một tập hợp các yếu tố có liên quan hoặc tương tác lẫn nhau của một tổ chức nhằm thiết lập các chính sách và mục tiêu, cũng như các quy trình để đạt được các mục tiêu đó" (*set of interrelated or interacting elements of an organization to establish policies and objectives, as well as processes to achieve those objectives*).

---

### Sample #16: RAGAS-ISO-016
- **Question**: Khái niệm 'asset management system' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.5?
- **Ground Truth**: Khái niệm 'asset management system' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.5 được định nghĩa là: management system for asset management
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.5`

```turtle
# Retrieved RDF Subgraph Context
iso:term_asset_management_system a iso:Concept ;
  rdfs:label "asset management system" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.5" ;
  iso:definition "management system for asset management" ;
  iso:pdmRelevance "high" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'asset management system'** được định nghĩa như sau:

Theo tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.3.5**, **'asset management system'** được định nghĩa là: *"management system for asset management"* (hệ thống quản lý cho việc quản lý tài sản).

---

### Sample #17: RAGAS-ISO-017
- **Question**: Khái niệm 'policy' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.6?
- **Ground Truth**: Khái niệm 'policy' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.6 được định nghĩa là: intentions and direction of an organization as formally expressed by its top management
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.6`

```turtle
# Retrieved RDF Subgraph Context
iso:term_policy a iso:Concept ;
  rdfs:label "policy" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.6" ;
  iso:definition "intentions and direction of an organization as formally expressed by its top management" ;
  iso:pdmRelevance "low" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'policy'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.3.6** như sau:

"intentions and direction of an organization as formally expressed by its top management" (ý định và định hướng của một tổ chức được thể hiện một cách chính thức bởi ban lãnh đạo cấp cao).

---

### Sample #18: RAGAS-ISO-018
- **Question**: Khái niệm 'objective' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.7?
- **Ground Truth**: Khái niệm 'objective' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.7 được định nghĩa là: result to be achieved
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.7`

```turtle
# Retrieved RDF Subgraph Context
iso:term_objective a iso:Concept ;
  rdfs:label "objective" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.7" ;
  iso:definition "result to be achieved" ;
  iso:pdmRelevance "medium" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'objective'** được định nghĩa như sau:

Trong tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.3.7**, 'objective' được định nghĩa là: **"result to be achieved"** (kết quả cần đạt được).

---

### Sample #19: RAGAS-ISO-019
- **Question**: Khái niệm 'risk' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.8?
- **Ground Truth**: Khái niệm 'risk' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.8 được định nghĩa là: effect of uncertainty on objectives
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.8`

```turtle
# Retrieved RDF Subgraph Context
iso:term_risk a iso:Concept ;
  rdfs:label "risk" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.8" ;
  iso:definition "effect of uncertainty on objectives" ;
  iso:pdmRelevance "high" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'risk'** được định nghĩa như sau:

Theo tiêu chuẩn **ISO 55000:2024**, tại điều khoản **3.3.8**, **risk** được định nghĩa là: *"effect of uncertainty on objectives"* (ảnh hưởng của sự không chắc chắn đối với các mục tiêu).

---

### Sample #20: RAGAS-ISO-020
- **Question**: Khái niệm 'opportunity' được định nghĩa như thế nào trong tiêu chuẩn ISO 55000:2024 điều khoản 3.3.9?
- **Ground Truth**: Khái niệm 'opportunity' theo tiêu chuẩn ISO 55000:2024 điều khoản 3.3.9 được định nghĩa là: circumstance or set of circumstances that can be exploited to improve performance, exceed original objectives and/or intended results, pursue additional objectives, or achieve continual improvement
- **Standard Citation**: `ISO 55000:2024 Clause 3.3.9`

```turtle
# Retrieved RDF Subgraph Context
iso:term_opportunity a iso:Concept ;
  rdfs:label "opportunity" ;
  iso:provenanceStandard "ISO 55000:2024" ;
  iso:provenanceClause "3.3.9" ;
  iso:definition "circumstance or set of circumstances that can be exploited to improve performance, exceed original objectives and/or intended results, pursue additional objectives, or achieve continual improvement" ;
  iso:pdmRelevance "low" .
```

#### RAG Generated Answer:
Dựa trên Ngữ cảnh Đồ thị Tri thức được cung cấp, khái niệm **'opportunity'** được định nghĩa trong tiêu chuẩn **ISO 55000:2024**, điều khoản **3.3.9** như sau:

"Là hoàn cảnh hoặc một tập hợp các hoàn cảnh có thể được khai thác để cải thiện hiệu suất, vượt qua các mục tiêu ban đầu và/hoặc các kết quả dự kiến, theo đuổi các mục tiêu bổ sung, hoặc đạt được sự cải tiến liên tục" (*circumstance or set of circumstances that can be exploited to improve performance, exceed original objectives and/or intended results, pursue additional objectives, or achieve continual improvement*).

---
