import { api } from '$lib/api';
import type { IndexerConfig, Resp } from '$lib/types';
import type { PageLoad } from './$types';

/**
 * Load selected indexer configuration.
 *
 * @param route - Route parameters containing the indexer ID.
 * @returns Data used by the layout or page.
 */
export const load: PageLoad = async ({ params }) => {
  // get the indexer config
  let config: IndexerConfig = {};
  await api
    .get(`flow/indexer/${params.indexer_id}/config`)
    .json<Resp<IndexerConfig>>()
    .then(({ data }) => (config = data));

  return { config };
};
