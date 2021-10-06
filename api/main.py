import os
import logging
import uvicorn
from uuid import uuid4

from fastapi import FastAPI, Depends, BackgroundTasks

from adapters.db_mongo_adapter import MongoDbAdapter
from providers import CacheProvider, OverpassProvider
from dto import SearchConfigModel
from base_algo import BasicAlgorithm

app = FastAPI()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_cache_provider() -> CacheProvider:
    return CacheProvider(MongoDbAdapter(host=os.environ.get('MONGODB_HOST', '127.0.0.1'),
                                        db_name=os.environ.get('MONGODB_DATABASE', 'road_trip'),
                                        series_name=os.environ.get('MONGODB_SERIES', 'user_search'),
                                        username=os.environ.get('MONGODB_USER', 'mongodbuser'),
                                        password=os.environ.get('MONGODB_PASSWORD',
                                                                'your_mongodb_root_password')))


@app.post("/search")
def read_root(search_config: SearchConfigModel,
              background_tasks: BackgroundTasks,
              cache_provider: CacheProvider = Depends(get_cache_provider)):
    search_id = str(uuid4())
    search_config.id = search_id
    raw_search_config = search_config.construct_search_config()
    basic_algo = BasicAlgorithm(OverpassProvider(os.environ.get('OSM_URL', 'https://overpass-api.de/api/interpreter')),
                                cache_provider=cache_provider)
    try:
        cache_provider.save_user_search(raw_search_config)
        background_tasks.add_task(basic_algo.search_nodes_ways, raw_search_config)
        return {"id": search_id}
    except Exception as e:
        logger.error(str(e))
        return {"error": True}


@app.get("/search/{search_id}")
def read_item(search_id: str,
              cache_provider: CacheProvider = Depends(get_cache_provider)):
    user_search = cache_provider.get_user_search(search_id)
    user_search.pop("_id")
    return user_search


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
