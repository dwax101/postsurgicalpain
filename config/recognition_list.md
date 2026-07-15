# PRO Instrument Recognition List

Generated from `dictionary.py`. Classify using ONLY what is listed here. Do not count an instrument not on this list; do not open the dictionary source.

## Visual Analog Scale (VAS) *(endorsed)*
- `visual\s+analog(?:ue|ic)?\s+(?:pain\s+)?scale`
- `visual\s+analog(?:ue|ic)?\s+(?:pain\s+)?score`
- `\bVAS\b`
- `\bEVA\b`

## Numeric Rating Scale (NRS) *(endorsed)*
- `numeric(?:al)?\s+(?:pain\s+)?rating\s+scale`
- `\bNRS\b`
- `\bNPRS\b`
- `\bVNRS\b`
- `\bNRSr\b`
- `\bNRSm\b`

## Verbal Rating Scale (VRS)
- `verbal\s+rating\s+scale`
- `verbal\s+descriptor\s+scale`
- `\bVRS\b`

## Faces Pain Scale / Wong-Baker (FPS)
- `faces\s+pain\s+scale(?:[-\s]revised)?`
- `wong[-\s]?baker`
- `\bFPS(?:-R)?\b`
- `\bFACES\b`

## Brief Pain Inventory (BPI)
- `brief\s+pain\s+inventory`
- `\bBPI(?:-SF)?\b`

## Pain Interference (PROMIS/BPI domain) *(endorsed)*
- `pain\s+interference`

## McGill Pain Questionnaire (MPQ)
- `mcgill\s+pain\s+questionnaire`
- `\bMPQ\b`
- `\bSF-?MPQ\b`
- `pain\s+rating\s+index`
- `\bPRI\b`

## Pain Catastrophizing Scale (PCS)
- `pain\s+catastroph\w+\s+scale`
- `\bPCS\b`

## Neuropathic Pain Scale (NPS)
- `neuropathic\s+pain\s+scale`
- `\bNPS\b`

## Central Sensitization Inventory (CSI)
- `central\s+sensiti[sz]ation\s+inventory`
- `\bCSI\b`

## Pain Disability Index (PDI)
- `pain\s+disability\s+index`
- `\bPDI\b`

## painDETECT
- `pain\s?detect`
- `\bPD-?Q\b`

## DN4
- `\bDN-?4\b`
- `douleur\s+neuropathique`

## LANSS
- `\bLANSS\b`
- `leeds\s+assessment\s+of\s+neuropathic`

## Neuropathic Pain Symptom Inventory (NPSI)
- `\bNPSI\b`
- `neuropathic\s+pain\s+symptom\s+inventory`

## Quality of Recovery (QoR-15/40)
- `quality\s+of\s+recovery`
- `\bQoR-?\d+\b`
- `\bQOR-?\d+\b`
- `\bQoR\b`

## EQ-5D
- `\bEQ-?5D(?:-?[35]L)?\b`
- `euroqol`

## Short Form Health Survey (SF-36/12/VR-12)
- `\bSF-?36\b`
- `\bSF-?12\b`
- `\bSF-?8\b`
- `\bVR-?12\b`
- `\bRAND-?36\b`
- `short[-\s]form\s+(?:36|12|health\s+survey)`

## PROMIS
- `\bPROMIS\b`
- `patient[-\s]reported\s+outcomes?\s+measurement\s+information`

## WHOQOL
- `\bWHOQOL(?:-?BREF)?\b`
- `world\s+health\s+organi[sz]ation\s+quality\s+of\s+life`

## EORTC QLQ-C30
- `\bQLQ-?C?30\b`
- `\bEORTC\b`
- `european\s+organi[sz]ation\s+for\s+research\s+and\s+treatment\s+of\s+cancer`

## Oswestry Disability Index (ODI)
- `oswestry`
- `\bODI\b`

## Roland-Morris Disability Questionnaire (RMDQ)
- `roland[-\s]morris`
- `\bRMDQ\b`
- `\bRDQ\b`

## WOMAC
- `\bWOMAC\b`
- `western\s+ontario\s+and\s+mcmaster`
- `mcmaster\s+universities\s+osteoarthritis\s+index`

## KOOS / HOOS
- `\bKOOS\b`
- `\bHOOS\b`
- `knee\s+injury\s+and\s+osteoarthritis\s+outcome`
- `hip\s+disability\s+and\s+osteoarthritis\s+outcome`
- `osteoarthritis\s+outcome\s+score`

## DASH / QuickDASH
- `\bquick-?\s?DASH\b`
- `\bDASH\b`
- `disabilities\s+of\s+the\s+arm,?\s+shoulder`

## Oxford Knee/Hip Score (OKS/OHS)
- `oxford\s+knee\s+score`
- `oxford\s+hip\s+score`
- `\bOKS\b`
- `\bOHS\b`

## ASES (Amer. Shoulder & Elbow Surgeons) *(endorsed)*
- `american\s+shoulder\s+and\s+elbow\s+surgeons`
- `\bASES\b`

## Lysholm score
- `lysholm`

## SANE (Single Assessment Numeric Eval.)
- `single\s+assessment\s+numeric\s+evaluation`
- `\bSANE\b`

## Hospital Anxiety & Depression Scale (HADS)
- `hospital\s+anxiety\s+and\s+depression`
- `\bHADS\b`

## State-Trait Anxiety Inventory (STAI)
- `state[-\s]trait\s+anxiety`
- `state\s+anxiety\s+inventory`
- `\bSTAI\b`

## Patient Health Questionnaire (PHQ)
- `patient\s+health\s+questionnaire`
- `\bPHQ-?\d*\b`

## GAD-7 (anxiety)
- `generali[sz]ed\s+anxiety\s+disorder`
- `\bGAD-?7\b`

## Beck Depression Inventory (BDI)
- `beck\s+depression\s+inventory`
- `\bBDI(?:-II)?\b`

## Pittsburgh Sleep Quality Index (PSQI)
- `pittsburgh\s+sleep\s+quality`
- `\bPSQI\b`

## Insomnia Severity Index (ISI)
- `insomnia\s+severity\s+index`
- `\bISI\b`

## Richards-Campbell Sleep Questionnaire (RCSQ)
- `richards[-\s]campbell`
- `\bRCSQ\b`

## Tampa Scale of Kinesiophobia (TSK)
- `tampa\s+scale`
- `kinesiophobia`
- `\bTSK\b`

## APAIS (Amsterdam Preop Anxiety & Info Scale)
- `amsterdam\s+preoperative\s+anxiety`
- `\bAPAIS\b`

## Patient Global Impression of Change (PGIC)
- `patient\s+global\s+impression`
- `\bPGIC\b`
- `\bPGI-?C\b`

## Overall Benefit of Analgesia Score (OBAS)
- `overall\s+benefit\s+of\s+analgesia`
- `\bOBAS\b`

## Opioid-Related Symptom Distress Scale (ORSDS) *(endorsed)*
- `opioid[-\s]related\s+symptom\s+distress`
- `\bORSDS\b`
- `\bOR-?SDS\b`

## APS-POQ-R (Amer. Pain Society Patient Outcome Q.)
- `american\s+pain\s+society\s+patient\s+outcome`
- `\bAPS-?POQ(?:-R)?\b`

## Oral Health Impact Profile (OHIP-14)
- `oral\s+health\s+impact\s+profile`
- `\bOHIP-?\d*\b`

## POSAS (Patient & Observer Scar Assessment)
- `patient\s+and\s+observer\s+scar\s+assessment`
- `\bPOSAS\b`
- `observer\s+scar\s+assessment\s+scale`
