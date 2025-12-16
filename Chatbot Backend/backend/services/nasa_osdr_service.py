

import logging
import requests
from typing import List, Dict, Any, Optional
import asyncio
from config import settings

logger = logging.getLogger(__name__)

class NASAOSDRService:

    def __init__(self):

        self.api_key = "zd8ezmmaYcyRajdzsbtEEUqBtgdB1JU2umyLzD4K"
        self.base_url = "https://osdr.nasa.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NASA-SpaceX-Chatbot/1.0',
            'Accept': 'application/json'
        })

    async def search_studies(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:

        try:

            search_url = f"{self.base_url}/osdr/data/search"
            params = {
                'term': query,
                'from': 0,
                'size': max_results,
                'type': 'cgene,ebi_pride,mg_rast'
            }

            logger.info(f"NASA OSDR search: {search_url} with term='{query}', size={max_results}")

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(search_url, params=params, timeout=15)
            )

            logger.info(f"NASA OSDR response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                hits_data = data.get('hits', {})
                total_results = hits_data.get('total', 0) if isinstance(hits_data, dict) else 0
                actual_hits = hits_data.get('hits', []) if isinstance(hits_data, dict) else []

                logger.info(f"NASA OSDR found {total_results} total results, returning {len(actual_hits)} hits")

                studies = []

                for hit in actual_hits[:max_results]:
                    if isinstance(hit, dict) and '_source' in hit:
                        source = hit['_source']

                        study_info = {
                            'id': (source.get('Accession') or source.get('Study Identifier') or
                                  source.get('Data Source Accession') or hit.get('_id', '')),
                            'title': (source.get('Study Title') or source.get('Project Title') or
                                     'Untitled Study'),
                            'description': (source.get('Study Description') or
                                           source.get('Study Protocol Description') or
                                           source.get('Project Title', '')[:100] or
                                           'No description available'),
                            'organism': source.get('organism', []),
                            'data_source_type': source.get('Data Source Type', ''),
                            'flight_program': source.get('Flight Program', ''),
                            'space_program': source.get('Space Program', ''),
                            'study_factor_type': source.get('Study Factor Type', []),
                            'study_factor_name': source.get('Study Factor Name', ''),
                            'material_type': source.get('Material Type', ''),
                            'experiment_platform': source.get('Experiment Platform', ''),
                            'managing_nasa_center': source.get('Managing NASA Center', ''),
                            'project_link': source.get('Project Link', ''),
                            'source': 'NASA OSDR',
                            'url': f"https://osdr.nasa.gov/bio/repo/data/studies/{source.get('Accession', '')}" if source.get('Accession') else "",
                            'score': hit.get('_score', 0),
                            'highlight': hit.get('highlight', {}),
                            'raw_data': source
                        }
                        studies.append(study_info)

                        logger.info(f"  Found study: {study_info['title'][:50]}... (score: {study_info['score']})")

                logger.info(f"Successfully parsed {len(studies)} studies from NASA OSDR")
                return studies

            else:
                logger.error(f"NASA OSDR search failed with status {response.status_code}: {response.text[:200]}")
                return []

        except Exception as e:
            logger.error(f"Error searching NASA OSDR: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def get_study_metadata(self, study_id: str) -> Optional[Dict[str, Any]]:

        try:

            if study_id.startswith('OSD-'):

                numeric_id = study_id.replace('OSD-', '')
                logger.info(f"Extracted numeric ID '{numeric_id}' from OSD study ID '{study_id}'")
            elif study_id.startswith('mgp'):

                numeric_id = study_id
                logger.info(f"Using full mgp ID '{numeric_id}' for metadata call")
            else:

                numeric_id = study_id
                logger.info(f"Using study ID '{numeric_id}' as-is for metadata call")

            metadata_url = f"{self.base_url}/osdr/data/osd/meta/{numeric_id}"
            logger.info(f"Fetching NASA OSDR study metadata: {metadata_url}")

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(metadata_url, timeout=15)
            )

            logger.info(f"NASA OSDR metadata response status: {response.status_code}")

            if response.status_code == 200:
                metadata = response.json()
                logger.info(f"Successfully fetched metadata for study {study_id}")

                if isinstance(metadata, dict):

                    study_data = {}
                    if 'study' in metadata and isinstance(metadata['study'], dict):

                        study_obj = metadata['study']

                        if study_obj:
                            study_key = list(study_obj.keys())[0]
                            study_data = study_obj[study_key]
                            logger.info(f"Found study data under key: {study_key}")

                    structured_metadata = {
                        'study_id': study_id,
                        'numeric_id': numeric_id,
                        'title': (study_data.get('title') or study_data.get('studyTitle') or
                                 study_data.get('name') or f"NASA Study {study_id}"),
                        'description': (study_data.get('description') or study_data.get('studyDescription') or
                                       'Detailed NASA study data available'),
                        'factors': study_data.get('factors', []),
                        'publications': study_data.get('publications', []),
                        'protocols': study_data.get('protocols', []),
                        'samples': study_data.get('samples', []),
                        'assays': study_data.get('assays', []),
                        'organisms': study_data.get('organisms', []),
                        'characteristics': study_data.get('characteristics', []),
                        'funding': study_data.get('funding', {}),
                        'contacts': study_data.get('contacts', []),
                        'people': study_data.get('people', []),
                        'acknowledgments': study_data.get('acknowledgments', ''),
                        'release_date': study_data.get('releaseDate', ''),
                        'submission_date': study_data.get('submissionDate', ''),
                        'update_date': study_data.get('lastUpdateDate', ''),
                        'experiment_platform': study_data.get('experimentPlatform', ''),
                        'flight_program': study_data.get('flightProgram', ''),
                        'space_program': study_data.get('spaceProgram', ''),
                        'managing_center': study_data.get('managingNasaCenter', ''),
                        'ontology_sources': study_data.get('ontologySourceReferences', []),
                        'comments': study_data.get('comments', []),
                        'raw_metadata': metadata,
                        'study_data': study_data
                    }

                    if structured_metadata['title'] == f"NASA Study {study_id}":

                        for potential_title_field in ['studyTitle', 'projectTitle', 'experimentTitle']:
                            if potential_title_field in study_data and study_data[potential_title_field]:
                                structured_metadata['title'] = study_data[potential_title_field]
                                break

                        if structured_metadata['title'] == f"NASA Study {study_id}":
                            organisms = study_data.get('organisms', [])
                            if organisms and len(organisms) > 0:
                                if isinstance(organisms[0], dict):
                                    org_name = organisms[0].get('name', organisms[0].get('organism', ''))
                                else:
                                    org_name = str(organisms[0])
                                if org_name:
                                    structured_metadata['title'] = f"NASA Study: {org_name} Research"

                    if structured_metadata['description'] == 'Detailed NASA study data available':

                        desc_sources = [
                            'studyDescription', 'projectDescription', 'summary',
                            'experimentDescription', 'protocolDescription'
                        ]
                        for desc_field in desc_sources:
                            if desc_field in study_data and study_data[desc_field]:
                                structured_metadata['description'] = study_data[desc_field]
                                break

                        if structured_metadata['description'] == 'Detailed NASA study data available':
                            factors = study_data.get('factors', [])
                            protocols = study_data.get('protocols', [])

                            desc_parts = []
                            if factors:
                                factor_names = [f.get('name', str(f)) if isinstance(f, dict) else str(f) for f in factors[:2]]
                                desc_parts.append(f"Study factors: {', '.join(factor_names)}")

                            if protocols:
                                protocol_names = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in protocols[:2]]
                                desc_parts.append(f"Protocols: {', '.join(protocol_names)}")

                            if desc_parts:
                                structured_metadata['description'] = '. '.join(desc_parts)

                    logger.info(f"Structured metadata for {study_id}: Title='{structured_metadata['title'][:50]}...', Description='{structured_metadata['description'][:50]}...'")
                    return structured_metadata
                else:
                    logger.warning(f"Unexpected metadata format for study {study_id}: {type(metadata)}")
                    return None

            else:
                logger.warning(f"Failed to fetch metadata for study {study_id}: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"Error fetching study metadata for {study_id}: {e}")
            return None

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(metadata_url, timeout=10)
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved metadata for study {study_id}")
                return data
            else:
                logger.warning(f"Failed to get metadata for study {study_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting study metadata for {study_id}: {e}")
            return None

    async def get_study_files(self, study_id: str) -> List[Dict[str, Any]]:

        try:

            numeric_id = study_id.replace('OSD-', '') if 'OSD-' in study_id else study_id

            files_url = f"{self.base_url}/osdr/data/osd/files/{numeric_id}"

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(files_url, timeout=10)
            )

            if response.status_code == 200:
                data = response.json()
                files = []

                if 'studies' in data:
                    for study_key, study_data in data['studies'].items():
                        study_files = study_data.get('study_files', [])
                        for file_info in study_files:
                            file_data = {
                                'file_name': file_info.get('file_name', ''),
                                'category': file_info.get('category', ''),
                                'file_size': file_info.get('file_size', 0),
                                'download_url': f"{self.base_url}{file_info.get('remote_url', '')}" if file_info.get('remote_url') else '',
                                'description': file_info.get('description', ''),
                                'study_id': study_key
                            }
                            files.append(file_data)

                logger.info(f"Retrieved {len(files)} files for study {study_id}")
                return files
            else:
                logger.warning(f"Failed to get files for study {study_id}")
                return []

        except Exception as e:
            logger.error(f"Error getting study files for {study_id}: {e}")
            return []

    async def search_experiments(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:

        try:
            experiments_url = f"{self.base_url}/geode-py/ws/api/experiments"

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(experiments_url, timeout=10)
            )

            if response.status_code == 200:
                data = response.json()
                experiments = []

                query_terms = query.lower().split()

                for experiment in data.get('experiments', [])[:max_results]:
                    experiment_text = f"{experiment.get('title', '')} {experiment.get('description', '')}".lower()

                    if any(term in experiment_text for term in query_terms):
                        exp_info = {
                            'experiment_id': experiment.get('identifier', ''),
                            'title': experiment.get('title', ''),
                            'description': experiment.get('description', ''),
                            'type': 'experiment',
                            'source': 'NASA OSDR',
                            'api_endpoint': f"{self.base_url}/geode-py/ws/api/experiment/{experiment.get('identifier', '')}"
                        }
                        experiments.append(exp_info)

                logger.info(f"Found {len(experiments)} experiments from NASA OSDR for query: {query}")
                return experiments

            else:
                logger.warning(f"NASA OSDR experiments search failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching NASA OSDR experiments: {e}")
            return []

    async def search_missions(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:

        try:
            missions_url = f"{self.base_url}/geode-py/ws/api/missions"

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(missions_url, timeout=10)
            )

            if response.status_code == 200:
                data = response.json()
                missions = []

                query_terms = query.lower().split()

                for mission in data.get('missions', [])[:max_results]:
                    mission_text = f"{mission.get('identifier', '')} {mission.get('title', '')}".lower()

                    if any(term in mission_text for term in query_terms):
                        mission_info = {
                            'mission_id': mission.get('identifier', ''),
                            'title': mission.get('title', mission.get('identifier', '')),
                            'start_date': mission.get('startDate', ''),
                            'end_date': mission.get('endDate', ''),
                            'type': 'mission',
                            'source': 'NASA OSDR',
                            'api_endpoint': f"{self.base_url}/geode-py/ws/api/mission/{mission.get('identifier', '')}"
                        }
                        missions.append(mission_info)

                logger.info(f"Found {len(missions)} missions from NASA OSDR for query: {query}")
                return missions

            else:
                logger.warning(f"NASA OSDR missions search failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching NASA OSDR missions: {e}")
            return []

    async def comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:

        try:
            logger.info(f" Starting comprehensive NASA OSDR search for: '{query}'")

            studies = await self.search_studies(query, max_results=3)
            logger.info(f" Found {len(studies)} studies from initial search")

            detailed_studies = []
            for study in studies:
                study_id = study.get('id', '')
                if study_id:
                    logger.info(f" Fetching detailed metadata for study: {study_id}")
                    metadata = await self.get_study_metadata(study_id)
                    if metadata:

                        enhanced_study = {
                            **study,
                            'detailed_metadata': metadata,
                            'enhanced_title': metadata.get('title', study.get('title', '')),
                            'enhanced_description': metadata.get('description', study.get('description', '')),
                            'protocols': metadata.get('protocols', []),
                            'publications': metadata.get('publications', []),
                            'organisms': metadata.get('organisms', []),
                            'factors': metadata.get('factors', []),
                            'samples': metadata.get('samples', []),
                            'assays': metadata.get('assays', []),
                            'funding': metadata.get('funding', {}),
                            'contacts': metadata.get('contacts', []),
                            'flight_program': metadata.get('flight_program', ''),
                            'space_program': metadata.get('space_program', ''),
                            'managing_center': metadata.get('managing_center', ''),
                        }
                        detailed_studies.append(enhanced_study)
                        logger.info(f" Enhanced study: {enhanced_study['enhanced_title'][:50]}...")
                    else:

                        detailed_studies.append(study)
                        logger.warning(f"  Using basic data for study: {study_id}")
                else:

                    detailed_studies.append(study)

            experiments_task = self.search_experiments(query, max_results=2)
            missions_task = self.search_missions(query, max_results=2)

            experiments, missions = await asyncio.gather(
                experiments_task, missions_task,
                return_exceptions=True
            )

            if isinstance(experiments, Exception):
                logger.error(f"Experiments search failed: {experiments}")
                experiments = []
            if isinstance(missions, Exception):
                logger.error(f"Missions search failed: {missions}")
                missions = []

            results = {
                'studies': detailed_studies,
                'experiments': experiments,
                'missions': missions
            }

            total_results = len(detailed_studies) + len(experiments) + len(missions)
            logger.info(f" NASA OSDR comprehensive search complete: {total_results} total results")
            logger.info(f"    Studies (with metadata): {len(detailed_studies)}")
            logger.info(f"    Experiments: {len(experiments)}")
            logger.info(f"    Missions: {len(missions)}")

            return results

        except Exception as e:
            logger.error(f"Error in comprehensive NASA OSDR search: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {'studies': [], 'experiments': [], 'missions': []}