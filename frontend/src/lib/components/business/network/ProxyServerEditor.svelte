<script lang="ts" module>
  import type { HTTPProxy, Resp } from '$lib/types';

  type ProxyServerEditorProps = Partial<{
    id: number;
    name: string;
    protocol: 'http' | 'socks5';
    host: string;
    port: number;
    username: string | null;
    pw_length: number;
    onsave: (result: HTTPProxy) => void;
  }>;
</script>

<script lang="ts">
  import { enhance } from '$app/forms';
  import { api } from '$lib/api';
  import { Label, Modal } from '$lib/components';
  import { createFormSchema, createLoading } from '$lib/helpers';
  import { _ } from '$lib/i18n';
  import { icons } from '$lib/icons';

  let { id, name, protocol = 'http', host, port, username, pw_length, onsave }: ProxyServerEditorProps = $props();

  // the modal dialog instance
  let modal: Modal;
  export const showModal = () => modal.show();

  // the loading state and form schema
  const loading = createLoading();
  const schema = createFormSchema(({ text, number, password }) => ({
    name: text().maxlength(64),
    host: text().maxlength(255),
    port: number().min(1).max(65535),
    username: text().maxlength(64).required(false),
    password: password().maxlength(64).required(false)
  }));

  /**
   * Save or update the HTTP proxy server.
   *
   * @param data - Form data.
   */
  function upsert(data: FormData) {
    loading.start();
    const json: Record<string, unknown> = Object.fromEntries(data);
    json.id = id;
    api
      .post('network/proxy/upsert', { json })
      .json<Resp<HTTPProxy>>()
      .then(({ data }) => {
        modal.close();
        onsave?.(data);
        setTimeout(() => {
          // reset the form
          name = '';
          protocol = 'http';
          host = '';
          port = undefined;
          username = '';
        }, 200);
      })
      .finally(() => {
        loading.end();
      });
  }
</script>

<Modal
  icon={icons.serverLink}
  title={$_(id ? 'action.edit' : 'action.add', $_('entity.proxy_server'))}
  bind:this={modal}
>
  <form
    method="post"
    use:enhance={({ formData, cancel }) => {
      cancel();
      upsert(formData);
    }}
  >
    <fieldset class="fieldset">
      <Label required>{$_('field.name')}</Label>
      <input class="input w-full" bind:value={name} {...schema.name} />
      <Label required>{$_('field.protocol')}</Label>
      <div class="flex flex-wrap gap-4">
        <label class="flex cursor-pointer items-center gap-1.5">
          <input type="radio" class="radio radio-sm" name="protocol" value="http" bind:group={protocol} />
          <span class="text-sm">HTTP</span>
        </label>
        <label class="flex cursor-pointer items-center gap-1.5">
          <input type="radio" class="radio radio-sm" name="protocol" value="socks5" bind:group={protocol} />
          <span class="text-sm">SOCKS5</span>
        </label>
      </div>
      <div class="flex gap-2">
        <div class="w-3/4 space-y-1.5">
          <Label required>{$_('field.host')}</Label>
          <input placeholder="127.0.0.1" class="input w-full" bind:value={host} {...schema.host} />
        </div>
        <div class="w-1/4 space-y-1.5">
          <Label required>{$_('field.port')}</Label>
          <input placeholder="7890" class="input w-full" bind:value={port} {...schema.port} />
        </div>
      </div>
      <Label>{$_('field.username')}</Label>
      <input class="input w-full" bind:value={username} {...schema.username} />
      <Label>{$_('field.password')}</Label>
      <input placeholder={'•'.repeat(pw_length || 0)} class="input w-full" {...schema.password} disabled={!username} />
    </fieldset>
    <div class="modal-action">
      <button type="button" class="btn" onclick={() => modal.close()}>
        {$_('message.cancel')}
      </button>
      <button type="submit" class="btn btn-submit" disabled={$loading !== null}>
        {$_('message.confirm')}
        {#if $loading}
          <span class="loading loading-xs loading-dots"></span>
        {/if}
      </button>
    </div>
  </form>
</Modal>
