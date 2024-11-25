import os
from opensearchpy import OpenSearch

host = os.getenv("OPENSEARCH_HOST")
auth = ('admin', os.getenv("OPENSEARCH_ADMIN_PASSWORD"))

opensearch_client = OpenSearch(
    hosts=[{'host': host, 'port': None}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=False,
    ssl_show_warn=False
)

# opensearch_client.indices.delete(index='program-popularity-*')
# opensearch_client.indices.delete_index_template(name='program-popularity')
try:
    opensearch_client.indices.get_index_template(name='program-popularity')
except:
    opensearch_client.indices.put_index_template(
        name='program-popularity',
        body={
            'index_patterns': ['program-popularity-*'],
            "priority": 1,
            'template': {
                'settings': {
                    'index': {
                        'number_of_shards': 3,
                        'number_of_replicas': 0
                    }
                },
                'mappings': {
                    'properties': {
                        'day_part': {'type': 'text'},
                        'program_id': {'type': 'text'},
                        'program_rating': {'type': 'integer'},
                        'program_count': {'type': 'integer'},
                        'genre': {'type': 'text'},
                        'genre_rating': {'type': 'integer'},
                        'genre_count': {'type': 'integer'}
                    }
                }
            }
        }
    )


if not opensearch_client.indices.exists(index='program-popularity-index'):
    opensearch_client.indices.create(index="program-popularity-index")